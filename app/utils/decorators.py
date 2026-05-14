from functools import wraps

from flask import abort, redirect, session


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            return redirect("/login")

        return view_func(*args, **kwargs)

    return wrapped_view


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if not session.get("user_id"):
                return redirect("/login")

            if session.get("user_role") not in roles:
                abort(403)

            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator


def pro_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        user_id = session.get("user_id")

        if not user_id:
            return redirect("/login")

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
            return redirect("/login")

        from app.services.verification_service import has_approved_verification

        if not has_approved_verification(user_id):
            abort(403)

        return view_func(*args, **kwargs)

    return wrapped_view
