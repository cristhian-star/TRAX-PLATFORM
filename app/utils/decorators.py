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
