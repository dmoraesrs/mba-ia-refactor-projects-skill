"""Hash de senha com werkzeug (scrypt por padrão)."""

from werkzeug.security import check_password_hash, generate_password_hash

_HASH_PREFIXES = ("scrypt:", "pbkdf2:")


def hash_password(raw_password):
    return generate_password_hash(raw_password)


def verify_password(password_hash, raw_password):
    if not is_hashed(password_hash):
        return False
    return check_password_hash(password_hash, raw_password)


def is_hashed(value):
    return isinstance(value, str) and value.startswith(_HASH_PREFIXES)
