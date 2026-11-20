"""Proteção das rotas administrativas por token (header X-Admin-Token)."""

import hmac
from functools import wraps

from flask import request

from src.errors import ForbiddenError

ADMIN_TOKEN_HEADER = "X-Admin-Token"  # noqa: S105 - nome do header, não é segredo


def build_admin_guard(admin_token):
    """Sem ADMIN_TOKEN configurado, as rotas administrativas ficam bloqueadas."""

    def require_admin(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            provided = request.headers.get(ADMIN_TOKEN_HEADER, "")
            if not admin_token or not hmac.compare_digest(provided.encode(), admin_token.encode()):
                raise ForbiddenError("Acesso administrativo negado")
            return view(*args, **kwargs)

        return wrapper

    return require_admin
