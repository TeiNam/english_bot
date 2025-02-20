# middlewares/https.py
from typing import Callable

from fastapi import Request
from fastapi.responses import RedirectResponse


async def https_redirect_middleware(request: Request, call_next: Callable):
    if request.url.scheme == "http" or request.headers.get("x-forwarded-proto") == "http":
        https_url = str(request.url.replace(scheme="https"))
        return RedirectResponse(https_url, status_code=307)
    return await call_next(request)
