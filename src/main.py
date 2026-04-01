from fastapi import (
    FastAPI, APIRouter, Depends, Response
)
from fastapi.staticfiles import StaticFiles
from fastapi_csrf_protect import CsrfProtect
from fastapi.middleware.cors import CORSMiddleware
from src.calls.router import router as calls_router
from src.users.router import router as users_router
from src.auth.router import router as auth_router
from src.middlewares import CSRFMiddleware


app = FastAPI()

app.add_middleware(CSRFMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory="media"), name="media")

api_v1_router = APIRouter(prefix="/api/v1")

@api_v1_router.get("/csrf-token")
def get_csrf_token(
    response: Response,
    csrf_protect: CsrfProtect = Depends()
):
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    csrf_protect.set_csrf_cookie(
        signed_token, response
    )
    return {"csrf_token": csrf_token}

api_v1_router.include_router(calls_router, prefix="/calls", tags=["Calls"])
api_v1_router.include_router(users_router, prefix="/users", tags=["Users"])
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Auth"])

app.include_router(api_v1_router)
