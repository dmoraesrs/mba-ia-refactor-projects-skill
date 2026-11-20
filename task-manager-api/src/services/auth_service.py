"""Autenticação: login com senha, emissão e validação do token de acesso."""

import logging

from src.errors import ForbiddenError, UnauthorizedError
from src.models import User

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, session, token_signer):
        self._session = session
        self._signer = token_signer

    def login(self, email, password):
        user = User.find_by_email(email)
        if not user or not user.check_password(password):
            raise UnauthorizedError("Credenciais inválidas")
        if not user.active:
            raise ForbiddenError("Usuário inativo")

        if user.has_legacy_password_hash():
            user.set_password(password)  # migra o hash MD5 antigo para scrypt
            self._session.commit()
            logger.info("Hash de senha migrado: user_id=%s", user.id)

        return user, self._signer.issue(user.id)

    def user_from_token(self, token):
        user_id = self._signer.read_user_id(token) if token else None
        user = User.find_by_id(user_id) if user_id is not None else None
        if not user or not user.active:
            raise UnauthorizedError("Token inválido ou expirado")
        return user
