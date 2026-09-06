from functools import wraps

from flask import abort, redirect, request, session, url_for


def _login_redirect():
    next_url = request.full_path.rstrip("?")
    return redirect(url_for("auth.login", next=next_url))


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        user_id = session.get("user_id")

        if not user_id:
            return _login_redirect()

        from app.models.user import User
        from app.services.user_service import is_user_active

        user = User.query.get(user_id)

        if not is_user_active(user):
            session.clear()
            return redirect("/login")

        return view_func(*args, **kwargs)

    return wrapped_view


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            user_id = session.get("user_id")

            if not user_id:
                return _login_redirect()

            from app.models.user import User
            from app.services.user_service import is_user_active

            user = User.query.get(user_id)

            if not is_user_active(user):
                session.clear()
                return redirect("/login")

            session["user_role"] = user.rol

            if user.rol not in roles:
                abort(403)

            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator


def pro_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        user_id = session.get("user_id")

        if not user_id:
            return _login_redirect()

        from app.services.subscription_service import has_pro_access

        if not has_pro_access(user_id):
            abort(403)

        return view_func(*args, **kwargs)

    return wrapped_view


def verified_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        user_id = session.get("user_id")

        if not user_id:
            return _login_redirect()

        from app.services.verification_service import has_approved_verification

        if not has_approved_verification(user_id):
            abort(403)

        return view_func(*args, **kwargs)

    return wrapped_view


def profile_complete_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        user_id = session.get("user_id")

        if not user_id:
            return _login_redirect()

        from app.models.professional import Professional

        professional = Professional.query.filter_by(user_id=user_id).first()

        if professional is None or not professional.perfil_completo:
            return redirect("/profesional/perfil/completar")

        return view_func(*args, **kwargs)

    return wrapped_view
