"""Casos de uso de tasks: listar, buscar, criar, atualizar e remover."""

import logging

from src.clock import utcnow_naive
from src.errors import NotFoundError
from src.models import Category, Task, User

logger = logging.getLogger(__name__)


def _is_id(value):
    return isinstance(value, int) and not isinstance(value, bool)


class TaskService:
    def __init__(self, session, notification_service):
        self._session = session
        self._notifications = notification_service

    # Leitura --------------------------------------------------------------
    def list_tasks(self):
        now = utcnow_naive()
        return [task.to_list_dict(now) for task in Task.list_with_relations()]

    def get_task(self, task_id):
        task = Task.find_by_id(task_id)
        if not task:
            raise NotFoundError("Task não encontrada")
        return task

    def search(self, filters):
        return [task.to_dict() for task in Task.search(**filters)]

    # Escrita --------------------------------------------------------------
    def create_task(self, fields):
        assignee = self._require_user(fields["user_id"]) if fields["user_id"] else None
        if fields["category_id"]:
            self._require_category(fields["category_id"])

        task = Task(**fields)
        self._session.add(task)
        self._session.commit()
        logger.info("Task criada: id=%s", task.id)

        if assignee:
            self._notifications.notify_task_assigned(assignee, task)
        return task

    def update_task(self, task, fields):
        new_assignee = None
        if fields.get("user_id"):
            new_assignee = self._require_user(fields["user_id"])
        if fields.get("category_id"):
            self._require_category(fields["category_id"])

        reassigned = new_assignee is not None and new_assignee.id != task.user_id
        for name, value in fields.items():
            setattr(task, name, value)
        task.updated_at = utcnow_naive()
        self._session.commit()
        logger.info("Task atualizada: id=%s", task.id)

        if reassigned:
            self._notifications.notify_task_assigned(new_assignee, task)
        return task

    def delete_task(self, task_id):
        task = self.get_task(task_id)
        self._session.delete(task)
        self._session.commit()
        logger.info("Task deletada: id=%s", task_id)

    # Apoio ----------------------------------------------------------------
    @staticmethod
    def _require_user(user_id):
        user = User.find_by_id(user_id) if _is_id(user_id) else None
        if not user:
            raise NotFoundError("Usuário não encontrado")
        return user

    @staticmethod
    def _require_category(category_id):
        category = Category.find_by_id(category_id) if _is_id(category_id) else None
        if not category:
            raise NotFoundError("Categoria não encontrada")
        return category
