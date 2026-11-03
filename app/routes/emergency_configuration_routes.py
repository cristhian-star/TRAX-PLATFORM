from flask import Blueprint, abort, render_template, request, session, redirect, url_for
from sqlalchemy.exc import SQLAlchemyError
from app.utils.decorators import role_required
from app import limiter
from app.utils.security import user_rate_limit_key
from app.services import emergency_configuration_service as service
from app.services.professional_workspace_service import build_workspace
from app.services.google_maps_config_service import obtener_google_maps_api_key
from app.services.coverage_service import DEFAULT_COVERAGE_CENTER, MAX_COVERAGE_RADIUS_KM

emergency_configuration = Blueprint('emergency_configuration', __name__)


@emergency_configuration.route('/profesional/urgencias/configuracion', methods=['GET','POST'])
@role_required('PROFESIONAL')
@limiter.limit('30 per hour', key_func=user_rate_limit_key, methods=['POST'])
def configure():
    actor = session['user_id']
    try:
        professional, values = service.initial(actor)
    except PermissionError:
        abort(403)
    error, status, review = None, 200, None
    if request.method == 'POST':
        allowed = set(values) | {'coverage_location_consent','impact_key','accept_impact'}
        values.update({k:request.form.get(k,'') for k in allowed if k in request.form})
        for checkbox in ('discount_repair','package_amount_free','visit_amount_free','diagnosis_amount_free','coverage_location_consent'):
            values[checkbox] = request.form.get(checkbox,'')
        try:
            if any(len(request.form.getlist(k)) != 1 for k in request.form):
                raise ValueError('Enviá un solo valor por campo.')
            result = service.save(actor,request.form)
            if result['saved']:
                return redirect(url_for('emergency_configuration.configure', saved='1'), code=303)
            review = result
            if result.get('error'):
                error, status = result['error'], 409
        except PermissionError as exc:
            error, status = str(exc), 403
        except service.ConfigurationConflict as exc:
            error, status = str(exc), 409
        except ValueError as exc:
            error, status = str(exc), 400
        except SQLAlchemyError:
            error, status = 'No pudimos guardar. Reintentá con el mismo formulario.', 503
    return render_template('emergency_configuration.html', workspace=build_workspace(actor),
        values=values, professional=professional, error=error, review=review,
        google_maps_api_key=obtener_google_maps_api_key(), center=DEFAULT_COVERAGE_CENTER,
        max_radius=MAX_COVERAGE_RADIUS_KM), status
