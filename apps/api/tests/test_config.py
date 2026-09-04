from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config import Settings, get_settings


def test_hosted_beta_requires_a_non_local_https_cors_origin() -> None:
    settings = Settings(
        app_env="hosted_beta",
        cors_origins="https://beta.example.test",
    )

    assert settings.app_env == "hosted_beta"
    assert settings.cors_origins == ["https://beta.example.test"]

    with pytest.raises(ValidationError):
        Settings(app_env="hosted_beta", cors_origins="http://localhost:5173")


def test_cors_wildcard_and_unknown_environment_fail_closed() -> None:
    with pytest.raises(ValidationError):
        Settings(cors_origins="*")
    with pytest.raises(ValidationError):
        Settings(app_env="hosted_beta_live", cors_origins="https://beta.example.test")


def test_json_and_comma_separated_origins_are_supported() -> None:
    json_origins = '["http://localhost:5173", "http://127.0.0.1:5173"]'
    assert Settings(cors_origins=json_origins).cors_origins == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    assert Settings(cors_origins="http://localhost:5173,http://127.0.0.1:5173").cors_origins == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


@pytest.mark.parametrize(
    "value, expected",
    [
        ('["http://localhost:5173"]', ["http://localhost:5173"]),
        ("http://localhost:5173,http://127.0.0.1:5173", [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]),
    ],
)
def test_cors_origins_from_environment_uses_the_same_safe_parser(
    monkeypatch: pytest.MonkeyPatch, value: str, expected: list[str]
) -> None:
    monkeypatch.setenv("CORS_ORIGINS", value)
    get_settings.cache_clear()

    assert get_settings().cors_origins == expected

    get_settings.cache_clear()
