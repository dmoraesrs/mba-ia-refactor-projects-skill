"""Relógio da aplicação: UTC sem tzinfo, compatível com as colunas DateTime naive já gravadas."""

from datetime import datetime, timezone


def utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)
