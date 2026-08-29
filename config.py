from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str
    DB_URL: str
    ADMIN_IDS: list[int] | int = Field(default_factory=list)

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            # Agar vergul bilan yoki bitta raqam bo'lib yozilsa, listga o'tkazib beradi
            return [int(x.strip()) for x in v.split(",") if x.strip().isdigit()]
        elif isinstance(v, int):
            return [v]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()