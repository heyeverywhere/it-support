from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str = Field(default="", validation_alias="BOT_TOKEN")
    database_url: str = Field(
        default="sqlite+aiosqlite:///./it_support.db",
        validation_alias="DATABASE_URL",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="REDIS_URL",
    )
    admin_ids: str = Field(default="", validation_alias="ADMIN_IDS")
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def admin_id_list(self) -> list[int]:
        if not self.admin_ids.strip():
            return []

        result = []

        for value in self.admin_ids.split(","):
            value = value.strip()

            if value.isdigit():
                result.append(int(value))

        return result


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()