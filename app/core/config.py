from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DATABASE_URL: str
    DATABASE_ECHO: bool = False
    AUTH_COOKIE_PATH: str = "/api/v1/auth"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
