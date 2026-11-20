"""Configuração da aplicação lida de variáveis de ambiente.

Nenhum segredo tem valor real como default: sem a variável, gera-se um valor
aleatório válido só para o processo atual (desenvolvimento) e o composition
root registra um aviso.
"""

import os
import secrets
from dataclasses import dataclass, field


def _bool(value):
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _list(value, default):
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    secret_key: str
    debug: bool
    host: str
    port: int
    database_path: str
    app_env: str
    admin_token: str
    cors_origins: list
    log_level: str
    seed_admin_password: str
    seed_customer_password: str
    generated: tuple = field(default_factory=tuple)  # variáveis ausentes que receberam valor aleatório


def load_settings():
    generated = []

    def secret(name):
        value = os.environ.get(name)
        if value:
            return value
        generated.append(name)
        return secrets.token_urlsafe(32)

    return Settings(
        secret_key=secret("SECRET_KEY"),
        debug=_bool(os.environ.get("FLASK_DEBUG")),
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        database_path=os.environ.get("DATABASE_PATH", "loja.db"),
        app_env=os.environ.get("APP_ENV", "producao"),
        admin_token=os.environ.get("ADMIN_TOKEN", ""),
        cors_origins=_list(os.environ.get("CORS_ORIGINS"), ["*"]),
        log_level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        seed_admin_password=secret("SEED_ADMIN_PASSWORD"),
        seed_customer_password=secret("SEED_CUSTOMER_PASSWORD"),
        generated=tuple(generated),
    )
