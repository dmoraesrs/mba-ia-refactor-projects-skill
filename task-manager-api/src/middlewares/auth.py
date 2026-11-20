"""Autenticação por token Bearer (emitido em POST /login) e checagem de papel."""

from functools import wraps

from flask import g, request

from src.errors import ForbiddenError, UnauthorizedError

BEARER_PREFIX = "Bearer "


class Authenticator:
    def __init__(self, auth_service):
        self._auth_service = auth_service

    def current_user(self):
        """Usuário autenticado da requisição; levanta 401 se não houver token válido."""
        if "current_user" in g:
            return g.current_user
        header = request.headers.get("Authorization", "")
        if not header.startswith(BEARER_PREFIX):
            raise UnauthorizedError("Autenticação necessária")
        g.current_user = self._auth_service.user_from_token(header[len(BEARER_PREFIX):].strip())
        return g.current_user

    def require_admin_user(self):
        user = self.current_user()
        if not user.is_admin():
            raise ForbiddenError("Acesso restrito a administradores")
        return user

    def login_required(self, view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            self.current_user()
            return view(*args, **kwargs)

        return wrapper

    def admin_required(self, view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            self.require_admin_user()
            return view(*args, **kwargs)

        return wrapper
