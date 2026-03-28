from fastapi import Request, Response
from fastapi_csrf_protect import CsrfProtect
from starlette.middleware.base import BaseHTTPMiddleware


class CSRFMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            csrf_protect = CsrfProtect()
            try:
                await csrf_protect.validate_csrf(request)
            except Exception:
                return Response("CSRF validation failed", status_code=403)
            
        response = await call_next(request)
        return response
