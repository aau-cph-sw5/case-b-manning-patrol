"""
Rate limiting

Per-client request limits for every API endpoint, built on slowapi.
"""

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120/minute"],
    strategy="moving-window",
    headers_enabled=True,
)


def rate_limit(request: Request, response: Response) -> None:
    """Count the request against the client's limit for the matched endpoint.

    Meant as an app-wide FastAPI dependency. It runs after routing, so it
    sees the endpoint of routes added with `include_router`, which slowapi's
    middleware cannot do
    """
    limiter._check_request_limit(request, request.scope["endpoint"], False)
    current_limit = getattr(request.state, "view_rate_limit", None)
    if current_limit is not None:
        limiter._inject_headers(response, current_limit)
