from flask import abort, request, session
from flask_limiter.util import get_remote_address


DEFAULT_PER_PAGE = 24
MAX_PER_PAGE = 50
MAX_PAGE = 1000
MAX_FILTER_LENGTH = 120


def client_ip():
    return get_remote_address() or "unknown"


def ip_rate_limit_key():
    return f"ip:{client_ip()}"


def user_or_ip_rate_limit_key():
    user_id = session.get("user_id")
    if user_id:
        return f"user:{user_id}:ip:{client_ip()}"

    return ip_rate_limit_key()


def user_rate_limit_key():
    user_id = session.get("user_id")
    if user_id:
        return f"user:{user_id}"

    return ip_rate_limit_key()


def normalize_limited_text(value, max_length=MAX_FILTER_LENGTH):
    value = (value or "").strip()
    if len(value) > max_length:
        abort(400)

    return value


def normalize_positive_int(value, default, minimum=1, maximum=None):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default

    parsed = max(parsed, minimum)
    if maximum is not None:
        parsed = min(parsed, maximum)

    return parsed


def get_pagination_params(default_per_page=DEFAULT_PER_PAGE, max_per_page=MAX_PER_PAGE):
    page = normalize_positive_int(request.args.get("page"), 1, minimum=1, maximum=MAX_PAGE)
    per_page = normalize_positive_int(
        request.args.get("per_page"),
        default_per_page,
        minimum=1,
        maximum=max_per_page,
    )
    return page, per_page


def paginate_items(items, page=None, per_page=None):
    if page is None or per_page is None:
        page, per_page = get_pagination_params()

    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end]


def wants_json_response():
    return request.accept_mimetypes.best == "application/json" or request.is_json
