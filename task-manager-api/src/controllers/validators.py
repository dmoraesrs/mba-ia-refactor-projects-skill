"""Validação de entrada centralizada. As mensagens são as mesmas da versão anterior da API."""

from datetime import datetime

from src.constants import (
    COLOR_PATTERN,
    DEFAULT_CATEGORY_COLOR,
    DEFAULT_PRIORITY,
    DEFAULT_ROLE,
    DEFAULT_TASK_STATUS,
    DUE_DATE_FORMAT,
    EMAIL_PATTERN,
    MIN_PASSWORD_LENGTH,
    PRIORITY_MAX,
    PRIORITY_MIN,
    TAGS_SEPARATOR,
    TASK_STATUSES,
    TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH,
    USER_ROLES,
)
from src.errors import ValidationError

INVALID_DATA = "Dados inválidos"
PRIORITY_RANGE_MESSAGE = f"Prioridade deve ser entre {PRIORITY_MIN} e {PRIORITY_MAX}"


# Genéricos -----------------------------------------------------------------
def require_body(data):
    """Corpo ausente, vazio ou que não é objeto JSON."""
    if not data or not isinstance(data, dict):
        raise ValidationError(INVALID_DATA)
    return data


def require_object(data):
    """Corpo precisa ser objeto JSON, mas pode ser vazio ({} não altera nada)."""
    if not isinstance(data, dict):
        raise ValidationError(INVALID_DATA)
    return data


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _coerce_id(value):
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return value or None


def _optional_text(value, message):
    if value is not None and not isinstance(value, str):
        raise ValidationError(message)
    return value


# Tasks ---------------------------------------------------------------------
def _validate_title(title):
    if not isinstance(title, str):
        raise ValidationError("Título inválido")
    if len(title) < TITLE_MIN_LENGTH:
        raise ValidationError("Título muito curto")
    if len(title) > TITLE_MAX_LENGTH:
        raise ValidationError("Título muito longo")
    return title


def _validate_status(status):
    if status not in TASK_STATUSES:
        raise ValidationError("Status inválido")
    return status


def _validate_priority(priority):
    if not _is_int(priority):
        raise ValidationError("Prioridade inválida")
    if priority < PRIORITY_MIN or priority > PRIORITY_MAX:
        raise ValidationError(PRIORITY_RANGE_MESSAGE)
    return priority


def _parse_due_date(value, message):
    if not isinstance(value, str):
        raise ValidationError(message)
    try:
        return datetime.strptime(value, DUE_DATE_FORMAT)
    except ValueError:
        raise ValidationError(message) from None


def _normalize_tags(tags):
    if isinstance(tags, list):
        if not all(isinstance(tag, str) for tag in tags):
            raise ValidationError("Tags inválidas")
        return TAGS_SEPARATOR.join(tags)
    return _optional_text(tags, "Tags inválidas")


def validate_task_create(data):
    require_body(data)
    title = data.get("title")
    if not title:
        raise ValidationError("Título é obrigatório")

    due_date = data.get("due_date")
    tags = data.get("tags")
    return {
        "title": _validate_title(title),
        "description": _optional_text(data.get("description", ""), "Descrição inválida"),
        "status": _validate_status(data.get("status", DEFAULT_TASK_STATUS)),
        "priority": _validate_priority(data.get("priority", DEFAULT_PRIORITY)),
        "user_id": _coerce_id(data.get("user_id")),
        "category_id": _coerce_id(data.get("category_id")),
        "due_date": _parse_due_date(due_date, "Formato de data inválido. Use YYYY-MM-DD") if due_date else None,
        "tags": _normalize_tags(tags) if tags else None,
    }


def validate_task_update(data):
    require_body(data)
    fields = {}
    if "title" in data:
        fields["title"] = _validate_title(data["title"])
    if "description" in data:
        fields["description"] = _optional_text(data["description"], "Descrição inválida")
    if "status" in data:
        fields["status"] = _validate_status(data["status"])
    if "priority" in data:
        fields["priority"] = _validate_priority(data["priority"])
    if "user_id" in data:
        fields["user_id"] = _coerce_id(data["user_id"])
    if "category_id" in data:
        fields["category_id"] = _coerce_id(data["category_id"])
    if "due_date" in data:
        due_date = data["due_date"]
        fields["due_date"] = _parse_due_date(due_date, "Formato de data inválido") if due_date else None
    if "tags" in data:
        fields["tags"] = _normalize_tags(data["tags"])
    return fields


def parse_search_filters(args):
    def optional_int(name, message):
        raw = args.get(name, "")
        if not raw:
            return None
        try:
            return int(raw)
        except ValueError:
            raise ValidationError(message) from None

    return {
        "text": args.get("q", ""),
        "status": args.get("status", ""),
        "priority": optional_int("priority", "Prioridade inválida"),
        "user_id": optional_int("user_id", "Usuário inválido"),
    }


# Users ---------------------------------------------------------------------
def _validate_email(email):
    if not isinstance(email, str) or not EMAIL_PATTERN.match(email):
        raise ValidationError("Email inválido")
    return email


def _validate_password(password, message):
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(message)
    return password


def validate_role(role):
    if role not in USER_ROLES:
        raise ValidationError("Role inválido")
    return role


def _validate_name(name):
    if not name or not isinstance(name, str):
        raise ValidationError("Nome é obrigatório")
    return name


def validate_user_create(data):
    """Valida tudo menos o role, que é checado depois do e-mail duplicado (ordem original)."""
    require_body(data)
    name, email, password = data.get("name"), data.get("email"), data.get("password")
    _validate_name(name)
    if not email:
        raise ValidationError("Email é obrigatório")
    if not password:
        raise ValidationError("Senha é obrigatória")
    return {
        "name": name,
        "email": _validate_email(email),
        "password": _validate_password(password, f"Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres"),
        "role": data.get("role", DEFAULT_ROLE),
    }


def validate_user_update(data):
    require_body(data)
    fields = {}
    if "name" in data:
        fields["name"] = _validate_name(data["name"])
    if "email" in data:
        fields["email"] = _validate_email(data["email"])
    if "password" in data:
        fields["password"] = _validate_password(data["password"], "Senha muito curta")
    if "role" in data:
        fields["role"] = validate_role(data["role"])
    if "active" in data:
        if not isinstance(data["active"], bool):
            raise ValidationError("Campo active inválido")
        fields["active"] = data["active"]
    return fields


def validate_login(data):
    require_body(data)
    email, password = data.get("email"), data.get("password")
    if not email or not password:
        raise ValidationError("Email e senha são obrigatórios")
    if not isinstance(email, str) or not isinstance(password, str):
        raise ValidationError("Email e senha são obrigatórios")
    return email, password


# Categories ----------------------------------------------------------------
def _validate_color(color):
    if not isinstance(color, str) or not COLOR_PATTERN.match(color):
        raise ValidationError("Cor inválida")
    return color


def validate_category_create(data):
    require_body(data)
    return {
        "name": _validate_name(data.get("name")),
        "description": _optional_text(data.get("description", ""), "Descrição inválida"),
        "color": _validate_color(data.get("color", DEFAULT_CATEGORY_COLOR)),
    }


def validate_category_update(data):
    require_object(data)
    fields = {}
    if "name" in data:
        fields["name"] = _validate_name(data["name"])
    if "description" in data:
        fields["description"] = _optional_text(data["description"], "Descrição inválida")
    if "color" in data:
        fields["color"] = _validate_color(data["color"])
    return fields
