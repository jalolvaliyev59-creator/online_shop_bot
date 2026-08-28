from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str
    DB_URL = "postgresql+asyncpg://online_shop_db_m4w3_user:psFnrhcBbfTtuUbenVG298OZEZ8McGie@dpg-da8hladg1s2s739eqbj0-a.ohio-postgres.render.com/online_shop_db_m4w3"
    ADMIN_IDS: list[int] = Field(default_factory=list)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()