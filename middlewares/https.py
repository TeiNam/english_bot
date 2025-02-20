# middlewares/https.py
from fastapi import Request
from fastapi.responses import RedirectResponse
from typing import Callable

async def https_redirect_middleware(request: Request, call_next: Callable):
    if request.url.scheme == "http":
        # HTTPS로 리다이렉트하되, 같은 포트 유지
        https_url = str(request.url.replace(scheme="https"))
        return RedirectResponse(https_url, status_code=307)
    return await call_next(request)