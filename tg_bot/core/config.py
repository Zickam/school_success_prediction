from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    API_URL: str = "http://app:8000/api/v1"

    BOT_TOKEN: str

    class Config:
        env_file = ("env/tg_bot.env", "env/app.env")
        case_sensitive = True
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
