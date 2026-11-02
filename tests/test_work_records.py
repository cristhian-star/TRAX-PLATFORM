"""Private records on the normal app factory, synthetic isolated SQLite."""
import unittest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from sqlalchemy import event
import tests.test_proposal_portal_p1 as fixtures
from app import db
from app.models.user import User
from app.models.professional import Professional
from app.models.work_record import WorkRecord, WorkFollowup, WorkReminder
from app.models.activity_notification import ActivityNotification
from app.models.contract_request import ContractRequest
from app.services import work_record_service as service

NOW=datetime(2026,10,30,15,tzinfo=timezone.utc)


def data(**changes):
    result=dict(title='Trabajo sintético',work_date='2026-10-29',client_name='Cliente manual',contact='PRIVATE_CONTACT',location='PRIVATE_LOCATION',notes='<script>PRIVATE_NOTES</script>\nSegunda línea',enabled='',reason='',advance_days='1',notice_time='09:00')
    result.update(changes)
    return result


def follow(**changes):
    result=data(enabled='on',reason='Mantenimiento',tentative_date='2026-11-05',remind_self='on')
    result.update(changes)
    return result


class WorkRecordsTest(unittest.TestCase):
    setUp=fixtures.ProposalPortalTest.setUp
    tearDown=fixtures.ProposalPortalTest.tearDown
    login=fixtures.ProposalPortalTest.login

    def save(self,payload=None,**kwargs):
        return service.save_record(2,payload or data(),str(uuid.uuid4()),clock=lambda:NOW,**kwargs)

    def contract(self):
        c=ContractRequest(cliente_id=1,professional_id=1,source_type='DIRECT',estado='CREADA',servicio='QA',professional_user_id=2)
        db.session.add(c);db.session.commit();return c.id

    def test_create_reload_edit_single_and_replay(self):
        with self.app.app_context():
            key=str(uuid.uuid4());rid=service.save_record(2,data(),key,clock=lambda:NOW)
            db.session.remove()
            self.assertEqual(service.save_record(2,data(),key,clock=lambda:NOW),rid)
            self.assertEqual(WorkRecord.query.count(),1)
            self.assertEqual(ContractRequest.query.count(),0)
            with self.assertRaises(service.WorkConflict):service.save_record(2,data(title='Otro'),key,clock=lambda:NOW)
            self.save(data(title='Editado'),record_id=rid,expected_version=1)
            self.assertEqual(db.session.get(WorkRecord,rid).version,2)
            with self.assertRaises(service.WorkConflict):self.save(data(),record_id=rid,expected_version=1)

    def test_direct_validation_limits_dates_options(self):
        cases=[('title',' '),('notes',' '),('title','x'*161),('notes','x'*10001),('client_name','x'*161),('contact','x'*255),('location','x'*301),('work_date','2026-02-30'),('enabled','hacked')]
        with self.app.app_context():
            for name,value in cases:
                with self.subTest(field=name),self.assertRaises(ValueError):self.save(data(**{name:value}))
            self.assertEqual(WorkRecord.query.count(),0)
            self.save(data(title='t'*160,notes='n'*10000,contact='c'*254,location='l'*300))
            for patch_data in [dict(tentative_date='2026-10-29'),dict(tentative_date='2026-10-30'),dict(advance_days='2'),dict(notice_time='25:00'),dict(reason='')]:
                with self.subTest(patch=patch_data),self.assertRaises(ValueError):self.save(follow(**patch_data))

    def test_follow_without_notices_past_notes_and_no_rearm(self):
        with self.app.app_context():
            rid=self.save(follow(remind_self=''))
            self.assertEqual(WorkReminder.query.count(),0)
            row=db.session.get(WorkRecord,rid);payload=service.record_data(row);payload['notes']='Changed'
            service.save_record(2,payload,str(uuid.uuid4()),rid,1,clock=lambda:NOW+timedelta(days=40))
            self.assertEqual(WorkReminder.query.count(),0)
            self.assertEqual(db.session.get(WorkRecord,rid).followup.version,1)

    def test_reminder_emit_retry_privacy_and_history(self):
        with self.app.app_context():
            cid=self.contract();rid=self.save(follow(contract_id=str(cid),remind_client='on'))
            self.assertEqual(WorkReminder.query.count(),2)
            due=datetime(2026,11,4,12,tzinfo=timezone.utc)
            self.assertEqual(service.dispatch_work_reminders(clock=lambda:due),2)
            self.assertEqual(service.dispatch_work_reminders(clock=lambda:due),0)
            client=ActivityNotification.query.filter_by(user_id=1,tipo='TRABAJO_SEGUIMIENTO').one()
            for secret in ('PRIVATE_NOTES','PRIVATE_CONTACT','PRIVATE_LOCATION'):self.assertNotIn(secret,client.mensaje)
            self.assertIsNone(client.url_destino)
            payload=service.record_data(db.session.get(WorkRecord,rid));payload['notes']='Only notes'
            self.save(payload,record_id=rid,expected_version=1)
            self.assertEqual(WorkReminder.query.count(),2)
            self.assertEqual(WorkReminder.query.filter_by(status='SENT').count(),2)

    def test_reschedule_disable_unlink_cancel_and_expiry(self):
        with self.app.app_context():
            rid=self.save(follow())
            self.save(follow(tentative_date='2026-12-05'),record_id=rid,expected_version=1)
            self.assertEqual(WorkReminder.query.filter_by(status='CANCELLED').count(),1)
            self.save(data(),record_id=rid,expected_version=2)
            self.assertEqual(WorkReminder.query.filter_by(status='PENDING').count(),0)
            rid2=self.save(follow())
            self.assertEqual(service.dispatch_work_reminders(clock=lambda:datetime(2026,11,6,12,tzinfo=timezone.utc)),0)
            self.assertEqual(WorkReminder.query.filter_by(status='SKIPPED').count(),1)

    def test_link_authorization_and_revalidation(self):
        with self.app.app_context():
            with self.assertRaises(ValueError):self.save(follow(remind_client='on'))
            with self.assertRaises(ValueError):self.save(follow(contract_id='999',remind_client='on'))
            cid=self.contract();rid=self.save(follow(contract_id=str(cid),remind_client='on',remind_self=''))
            c=db.session.get(ContractRequest,cid);c.professional_id=999
            # Simulate lost authorization without mutating a real contract outside this test.
            db.session.rollback()
            with patch.object(service,'linked_client',side_effect=ValueError('revoked')):
                self.assertEqual(service.dispatch_work_reminders(clock=lambda:datetime(2026,11,4,12,tzinfo=timezone.utc)),0)
            self.assertEqual(WorkReminder.query.one().status,'SKIPPED')

    def test_rollback_save_and_dispatch(self):
        with self.app.app_context():
            with patch.object(db.session,'commit',side_effect=RuntimeError('synthetic')):
                with self.assertRaises(RuntimeError):self.save(follow())
            self.assertEqual(WorkRecord.query.count(),0)
            rid=self.save(follow())
            with patch.object(service,'crear_notificacion',side_effect=RuntimeError('synthetic')):
                with self.assertRaises(RuntimeError):service.dispatch_work_reminders(clock=lambda:datetime(2026,11,4,12,tzinfo=timezone.utc))
            self.assertEqual(WorkReminder.query.one().status,'PENDING')
            self.assertEqual(service.dispatch_work_reminders(clock=lambda:datetime(2026,11,4,12,tzinfo=timezone.utc)),1)

    def test_permissions_ownership_replay_and_csrf(self):
        with self.app.app_context():
            key=str(uuid.uuid4());rid=service.save_record(2,data(),key,clock=lambda:NOW)
            with self.assertRaises(PermissionError):service.save_record(1,data(),key,clock=lambda:NOW)
            db.session.add(User(id=3,nombre='Other',email='other@qa.invalid',password='x',rol='PROFESIONAL',estado='ACTIVO'));db.session.commit()
            with self.assertRaises(LookupError):service.own_record(3,rid)
            with self.assertRaises(LookupError):service.save_record(3,data(),str(uuid.uuid4()),rid,1,clock=lambda:NOW)
        self.assertEqual(self.client.get('/profesional/trabajos').status_code,302)
        self.login(1);self.assertEqual(self.client.get('/profesional/trabajos').status_code,403)
        self.login(3);self.assertEqual(self.client.get(f'/profesional/trabajos/registros/{rid}').status_code,404)
        self.login();self.app.config['WTF_CSRF_ENABLED']=True
        self.assertEqual(self.client.post('/profesional/trabajos/registros/nuevo',data=data()).status_code,400)

    def test_filters_pagination_inclusive_and_get_no_writes(self):
        with self.app.app_context():
            for i in range(12):self.save(data(title=f'Trabajo {i}',client_name='Referencia',work_date='2026-10-29'))
        self.login()
        with self.app.app_context():
            writes=[]
            def track(conn,cursor,statement,parameters,context,many):
                if statement.lstrip().split()[0].upper() in ('INSERT','UPDATE','DELETE'):writes.append(statement)
            event.listen(db.engine,'before_cursor_execute',track)
            try:
                r=self.client.get('/profesional/trabajos?q=Trabajo&client=Referencia&from=2026-10-29&to=2026-10-29&follow=without')
                self.assertEqual(r.status_code,200);self.assertIn('12 registros',r.text);self.assertIn('page=2',r.text)
                self.assertFalse(writes)
            finally:event.remove(db.engine,'before_cursor_execute',track)
        for query in ('from=bad','from=2026-11-01&to=2026-10-01','page=-1','follow=bad'):
            self.assertEqual(self.client.get('/profesional/trabajos?'+query).status_code,400)
        self.assertIn('No encontramos',self.client.get('/profesional/trabajos?q=missing').text)
        self.assertEqual(self.client.get('/profesional/trabajos/contratados').status_code,200)

    def test_http_recovery_success_edit_and_safe_return(self):
        self.login();key=str(uuid.uuid4());payload=data(title='',command_key=key)
        r=self.client.post('/profesional/trabajos/registros/nuevo',data=payload)
        self.assertEqual(r.status_code,400);self.assertIn('&lt;script&gt;PRIVATE_NOTES',r.text)
        payload['title']='Saved';r=self.client.post('/profesional/trabajos/registros/nuevo',data=payload)
        self.assertEqual(r.location,'/profesional/trabajos')
        with self.app.app_context():rid=WorkRecord.query.one().id
        r=self.client.get(f'/profesional/trabajos/registros/{rid}?ret=https://evil.test')
        self.assertIn('href="/profesional/trabajos"',r.text)
        self.assertNotIn('<script>PRIVATE_NOTES',r.text)
        payload.update(title='Edited',version='1',command_key=str(uuid.uuid4()))
        r=self.client.post(f'/profesional/trabajos/registros/{rid}/editar',data=payload)
        self.assertEqual(r.status_code,302)
        self.assertIn('Edited',self.client.get(r.location).text)

    def test_unlink_cancels_client_and_late_self_dispatch(self):
        with self.app.app_context():
            cid=self.contract()
            rid=self.save(follow(contract_id=str(cid),remind_client='on'))
            payload=service.record_data(db.session.get(WorkRecord,rid))
            payload.update(contract_id='',remind_client=False)
            self.save(payload,record_id=rid,expected_version=1)
            self.assertEqual(WorkReminder.query.filter_by(audience='CLIENT',status='CANCELLED').count(),1)
            self.assertEqual(service.dispatch_work_reminders(clock=lambda:datetime(2026,11,5,20,tzinfo=timezone.utc)),1)
            self.assertEqual(ActivityNotification.query.filter_by(user_id=1).count(),0)
            self.assertEqual(service.dispatch_work_reminders(clock=lambda:datetime(2026,11,6,3,tzinfo=timezone.utc)),0)

    def test_signed_return_and_inactive_replay(self):
        from app.routes.work_record_routes import context_signer
        with self.app.app_context():
            key=str(uuid.uuid4());rid=service.save_record(2,data(),key,clock=lambda:NOW)
            token=context_signer().dumps([2,dict(q='Trabajo',page='2')])
        self.login()
        response=self.client.get(f'/profesional/trabajos/registros/{rid}?ret={token}')
        self.assertIn('/profesional/trabajos?q=Trabajo&amp;page=2',response.text)
        with self.app.app_context():
            db.session.get(User,2).estado='INACTIVO';db.session.commit()
            with self.assertRaises(PermissionError):service.save_record(2,data(),key,clock=lambda:NOW)

    def test_http_invalid_limits_no_side_effects(self):
        self.login()
        for changes in (dict(title='x'*161),dict(notes='x'*10001),dict(work_date='bad'),dict(enabled='invalid'),dict(contact='x'*255)):
            response=self.client.post('/profesional/trabajos/registros/nuevo',data=data(command_key=str(uuid.uuid4()),**changes))
            self.assertEqual(response.status_code,400)
        with self.app.app_context():
            self.assertEqual(WorkRecord.query.count(),0)
            self.assertEqual(WorkReminder.query.count(),0)
