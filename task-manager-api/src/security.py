"""Hash de senha (werkzeug/scrypt) e token de acesso assinado (itsdangerous)."""

import hashlib
import hmac
import re

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

_LEGACY_MD5_PATTERN = re.compile(r"^[0-9a-f]{32}$")
_TOKEN_SALT = "task-manager-auth-token"  # noqa: S105 - namespace do itsdangerous; o segredo é o SECRET_KEY


def hash_password(raw_password):
    return generate_password_hash(raw_password)


def is_legacy_hash(password_hash):
    """Hash MD5 sem salt gravado pela versão anterior da API."""
    return bool(password_hash) and bool(_LEGACY_MD5_PATTERN.match(password_hash))


def verify_password(password_hash, raw_password):
    if not password_hash:
        return False
    if is_legacy_hash(password_hash):
        # Só para migração: confere o hash antigo uma vez; o AuthService regrava com scrypt no login.
        legacy = hashlib.md5(raw_password.encode(), usedforsecurity=False).hexdigest()  # noqa: S324
        return hmac.compare_digest(legacy, password_hash)
    return check_password_hash(password_hash, raw_password)


class TokenSigner:
    """Emite e valida tokens assinados com a SECRET_KEY e com prazo de validade."""

    def __init__(self, secret_key, max_age_seconds):
        self._serializer = URLSafeTimedSerializer(secret_key, salt=_TOKEN_SALT)
        self._max_age = max_age_seconds

    def issue(self, user_id):
        return self._serializer.dumps({"user_id": user_id})

    def read_user_id(self, token):
        """Devolve o user_id do token ou None se o token for inválido ou expirado."""
        try:
            payload = self._serializer.loads(token, max_age=self._max_age)
        except (BadSignature, SignatureExpired):
            return None
        user_id = payload.get("user_id") if isinstance(payload, dict) else None
        return user_id if isinstance(user_id, int) else None
