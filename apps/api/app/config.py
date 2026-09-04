import json
from functools import lru_cache
from typing import Annotated, Final

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

SUPPORTED_APP_ENVS: Final = frozenset(
    {"local", "development", "internal_beta", "hosted_beta", "production"}
)
HOSTED_APP_ENVS: Final = frozenset({"hosted_beta", "production"})


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    # Do not let pydantic-settings decode this before ``parse_origins`` runs.
    # Deployment platforms pass environment variables as strings, and H1
    # intentionally accepts either an exact JSON array or a comma-separated list.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )
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

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        normalized = value.strip().casefold()
        if normalized not in SUPPORTED_APP_ENVS:
            allowed = ", ".join(sorted(SUPPORTED_APP_ENVS))
            raise ValueError(f"APP_ENV must be one of: {allowed}")
        return normalized

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                try:
                    return json.loads(stripped)
                except json.JSONDecodeError:
                    pass
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return value

    @field_validator("cors_origins")
    @classmethod
    def validate_origins(cls, value: list[str]) -> list[str]:
        normalized = [origin.strip().rstrip("/") for origin in value if origin.strip()]
        if not normalized:
            raise ValueError("CORS_ORIGINS must contain at least one exact origin")
        if any(origin == "*" for origin in normalized):
            raise ValueError("CORS_ORIGINS must not use a wildcard")
        if any(not origin.startswith(("http://", "https://")) for origin in normalized):
            raise ValueError("CORS_ORIGINS entries must include http:// or https://")
        return normalized

    @model_validator(mode="after")
    def validate_hosted_environment(self) -> "Settings":
        if self.app_env in HOSTED_APP_ENVS:
            if any(not origin.startswith("https://") for origin in self.cors_origins):
                raise ValueError(
                    "hosted_beta and production require exact https:// CORS_ORIGINS entries"
                )
            if any("localhost" in origin or "127.0.0.1" in origin for origin in self.cors_origins):
                raise ValueError(
                    "hosted_beta and production must not allow localhost CORS origins"
                )
        return self

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
