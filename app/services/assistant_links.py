"""Canonical relative links from registered backend routes, also outside HTTP."""
from flask import current_app


def canonical_url(endpoint, **values):
    adapter = current_app.url_map.bind("localhost", script_name=current_app.config.get("APPLICATION_ROOT", "/"))
    return adapter.build(endpoint, values, force_external=False)
