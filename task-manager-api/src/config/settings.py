"""Configuração da aplicação lida de variáveis de ambiente.

Nenhum segredo tem valor real como default. Sem SECRET_KEY, gera-se um valor
aleatório válido só para o processo atual (desenvolvimento) e o composition
root registra um aviso.
"""

import os
import secrets
from dataclasses import dataclass, field

DEFAULT_TOKEN_MAX_AGE_SECONDS = 8 * 60 * 60


def _bool(value):
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _list(value, default):
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class SmtpSettings:
    host: str
    port: int
    user: str
    password: str
    sender: str

    @property
    def enabled(self):
        return bool(self.host and self.user and self.password)


@dataclass(frozen=True)
class Settings:
    secret_key: str
    debug: bool
    host: str
    port: int
    database_url: str
    cors_origins: list
    log_level: str
    token_max_age: int
    smtp: SmtpSettings
    generated: tuple = field(default_factory=tuple)  # variáveis ausentes que receberam valor aleatório


def load_settings():
    generated = []

    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        generated.append("SECRET_KEY")
        secret_key = secrets.token_urlsafe(32)

    smtp_user = os.environ.get("SMTP_USER", "")
    return Settings(
        secret_key=secret_key,
        debug=_bool(os.environ.get("FLASK_DEBUG")),
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        database_url=os.environ.get("DATABASE_URL", "sqlite:///tasks.db"),
        cors_origins=_list(os.environ.get("CORS_ORIGINS"), ["*"]),
        log_level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        token_max_age=int(os.environ.get("TOKEN_MAX_AGE", str(DEFAULT_TOKEN_MAX_AGE_SECONDS))),
        smtp=SmtpSettings(
            host=os.environ.get("SMTP_HOST", ""),
            port=int(os.environ.get("SMTP_PORT", "587")),
            user=smtp_user,
            password=os.environ.get("SMTP_PASSWORD", ""),
            sender=os.environ.get("SMTP_SENDER", smtp_user),
        ),
        generated=tuple(generated),
    )
