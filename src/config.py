from pydantic_settings import BaseSettings
from pydantic import Field, BaseModel
from pathlib import Path
from fastapi_csrf_protect import CsrfProtect


BASE_DIR = Path(__file__).resolve().parent.parent

ENV_PATH = BASE_DIR / ".env"

class AuthJWT(BaseModel):
    private_key_path: Path = BASE_DIR / "certs" / "jwt_private.pem"
    public_key_path: Path = BASE_DIR / "certs" / "jwt_public.pem"
    access_token_expire_minutes: str = 30
    refresh_token_expire_days: str = 30
    algorithm: str = "RS256"


class Cookies(BaseModel):
    access_cookie_name: str = "access_token"
    refresh_cookie_name: str = "refresh_token"
    cookie_params: dict = {
        "httponly": True,
        "secure": True,
        "samesite": "lax",
        "path": "/",
    }


class Settings(BaseSettings):
    db_host: str = Field(..., env="DB_HOST")
    db_port: int = Field(..., env="DB_PORT")
    db_name: str = Field(..., env="DB_NAME")
    db_user: str = Field(..., env="DB_USER")
    db_password: str = Field(..., env="DB_PASSWORD")

    csrf_token: str = Field(..., env="CSRF_TOKEN")

    auth_jwt: AuthJWT = AuthJWT()
    cookies: Cookies = Cookies()

    media_dir: Path = Path("media")
    avatar_dir: Path = media_dir / "avatars"
    avatar_dir_prefix: str = "/media/avatars/"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    class Config:
        env_file = ENV_PATH
        env_file_encoding = "utf-8"


settings = Settings()

class CsrfSettings(BaseSettings):
    secret_key: str = settings.csrf_token
    cookie_samesite: str = "lax"
    cookie_key: str = "csrftoken"
    header_name: str = "X-CSRF-Token"


@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()
