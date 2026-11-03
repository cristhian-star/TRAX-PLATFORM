"""Professional-only private record interfaces."""
import uuid
from datetime import timezone
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
from itsdangerous import URLSafeSerializer, BadSignature
from flask import Blueprint, request, session, render_template, redirect, url_for, abort, current_app, flash
from app import db, limiter
from app.utils.decorators import role_required
from app.models.work_record import WorkReminder
from app.services.professional_workspace_service import build_workspace
from app.services import work_record_service as service

work_records=Blueprint('work_records',__name__)
BASE='/profesional/trabajos'


def context_signer():
    return URLSafeSerializer(current_app.config['SECRET_KEY'],salt='work-list-context')


def return_url(token):
    if not token:return BASE
    try:
        actor,query=context_signer().loads(token)
        if actor!=session['user_id'] or not isinstance(query,dict) or set(query)-{'q','client','from','to','follow','page'} or any(not isinstance(v,str) or len(v)>160 for v in query.values()):raise ValueError
        return BASE+'?'+urlencode(query)
    except (BadSignature,ValueError,TypeError):
        return BASE


def common():
    return dict(workspace=build_workspace(session['user_id']),limits=service.LIMITS)


def list_view():
    error=None;status=200
    try:
        context=service.list_records(session['user_id'],request.args)
    except ValueError as exc:
        error=str(exc);status=400
        context=dict(rows=[],total=0,page=1,has_next=False,filters={n:request.args.get(n,'')[:160] for n in ('q','client','from','to','follow')})
    token=context_signer().dumps([session['user_id'],context['filters']])
    def page_url(page):
        values=dict(context['filters']);values['page']=page
        return BASE+'?'+urlencode(values)
    return render_template('work_record_list.html',**common(),**context,error=error,return_token=token,page_url=page_url),status


@work_records.route('/profesional/trabajos/registros/nuevo',methods=['GET','POST'])
@work_records.route('/profesional/trabajos/registros/<int:record_id>/editar',methods=['GET','POST'])
@role_required('PROFESIONAL')
@limiter.limit('60 per hour',methods=['POST'])
def edit(record_id=None):
    actor=session['user_id'];row=None
    if record_id:
        try:row=service.own_record(actor,record_id)
        except LookupError:abort(404)
    form=service.record_data(row) if row else dict(work_date=service.local_today().isoformat(),advance_days=1,notice_time='09:00')
    key=str(uuid.uuid4());version=row.version if row else '';error=None;status=200
    token=request.values.get('ret','')
    if request.method=='POST':
        form={name:request.form.get(name,'') for name in (*service.LIMITS,'work_date','contract_id',*service.FOLLOW_FIELDS)}
        key=request.form.get('command_key','');version=request.form.get('version','')
        try:
            if request.form.get('action')=='link':
                raw=form.get('contract_id')
                service.linked_client(actor,int(raw)) if raw and raw.isdigit() else service.linked_client(actor,None)
                if not raw:form['remind_client']=''
            else:
                result=service.save_record(actor,form,key,record_id,version if record_id else None)
                flash('Registro guardado.','success')
                return redirect(url_for('work_records.detail',record_id=result,ret=token) if record_id else BASE)
        except service.WorkConflict as exc:
            error=str(exc);status=409
        except (ValueError,OverflowError) as exc:
            error=str(exc);status=400
        except PermissionError:abort(403)
    linked=None
    raw=form.get('contract_id')
    if raw:
        try:linked=service.linked_client(actor,int(raw))
        except (ValueError,TypeError):pass
    return render_template('work_record_form.html',**common(),form=form,key=key,version=version,row=row,
        linked=linked,client_options=service.client_options(actor),error=error,return_token=token,
        cancel_url=url_for('work_records.detail',record_id=record_id,ret=token) if row else BASE),status


@work_records.get('/profesional/trabajos/registros/<int:record_id>')
@role_required('PROFESIONAL')
def detail(record_id):
    try:row=service.own_record(session['user_id'],record_id)
    except LookupError:abort(404)
    reminders=WorkReminder.query.filter_by(record_id=row.id).order_by(WorkReminder.id.desc()).all()
    token=request.args.get('ret','')
    return render_template('work_record_detail.html',**common(),row=row,reminders=reminders,
        return_token=token,back_url=return_url(token), local_due=lambda value: value.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(service.ZONE)))
