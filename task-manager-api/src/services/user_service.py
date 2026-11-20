"""Casos de uso de usuários: cadastro, atualização, remoção em cascata e listagens."""

import logging

from src.errors import ConflictError, NotFoundError
from src.models import Task, User

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, session):
        self._session = session

    # Leitura --------------------------------------------------------------
    def list_users(self):
        task_counts = Task.count_by_user()
        result = []
        for user in User.list_all():
            data = user.to_dict()
            data["task_count"] = task_counts.get(user.id, (0, 0))[0]
            result.append(data)
        return result

    def get_user(self, user_id):
        user = User.find_by_id(user_id)
        if not user:
            raise NotFoundError("Usuário não encontrado")
        return user

    def get_user_with_tasks(self, user_id):
        user = self.get_user(user_id)
        data = user.to_dict()
        data["tasks"] = [task.to_dict() for task in Task.list_by_user(user_id)]
        return data

    def list_user_tasks(self, user_id):
        self.get_user(user_id)
        return [task.to_summary_dict() for task in Task.list_by_user(user_id)]

    # Escrita --------------------------------------------------------------
    def ensure_email_available(self, email, current_user_id=None):
        existing = User.find_by_email(email)
        if existing and existing.id != current_user_id:
            raise ConflictError("Email já cadastrado")

    def create_user(self, fields):
        user = User(name=fields["name"], email=fields["email"], role=fields["role"])
        user.set_password(fields["password"])
        self._session.add(user)
        self._session.commit()
        logger.info("Usuário criado: id=%s", user.id)
        return user

    def update_user(self, user, fields):
        if "email" in fields:
            self.ensure_email_available(fields["email"], current_user_id=user.id)
        for name, value in fields.items():
            if name == "password":
                user.set_password(value)
            else:
                setattr(user, name, value)
        self._session.commit()
        return user

    def delete_user(self, user_id):
        """Remove o usuário e as tasks dele na mesma transação."""
        user = self.get_user(user_id)
        Task.delete_by_user(user_id)
        self._session.delete(user)
        self._session.commit()
        logger.info("Usuário deletado: id=%s", user_id)
