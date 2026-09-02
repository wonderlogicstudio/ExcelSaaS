from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    cors_origins: list[str] = ["http://localhost:5173"]
    max_upload_mb: int = 10
    max_uncompressed_mb: int = 120
    max_zip_entries: int = 5000
    max_compression_ratio: int = 250
    scan_cell_limit: int = 250_000
    finding_limit: int = 120
    ai_explanations_enabled: bool = False
    formula_pattern_audit_enabled: bool = False
    formula_audit_max_formula_cells: int = Field(default=30_000, ge=1)
    formula_audit_max_sheet_count: int = Field(default=200, ge=1)
    formula_audit_max_candidate_count: int = Field(default=120, ge=1)
    file_retention_hours: int = 24

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def max_uncompressed_bytes(self) -> int:
        return self.max_uncompressed_mb * 1024 * 1024


FORMULA_AUDIT_INTERNAL_ENVS = frozenset({"development", "internal_beta"})


def formula_audit_is_available(settings: Settings) -> bool:
    """Fail closed outside the isolated internal-beta environments."""

    return (
        settings.formula_pattern_audit_enabled
        and settings.app_env.strip().casefold() in FORMULA_AUDIT_INTERNAL_ENVS
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
