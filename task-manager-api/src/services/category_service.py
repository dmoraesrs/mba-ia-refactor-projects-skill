"""Casos de uso de categorias."""

import logging

from src.errors import NotFoundError
from src.models import Category, Task

logger = logging.getLogger(__name__)


class CategoryService:
    def __init__(self, session):
        self._session = session

    def list_categories(self):
        task_counts = Task.count_by_category()
        result = []
        for category in Category.list_all():
            data = category.to_dict()
            data["task_count"] = task_counts.get(category.id, 0)
            result.append(data)
        return result

    def get_category(self, category_id):
        category = Category.find_by_id(category_id)
        if not category:
            raise NotFoundError("Categoria não encontrada")
        return category

    def create_category(self, fields):
        category = Category(**fields)
        self._session.add(category)
        self._session.commit()
        logger.info("Categoria criada: id=%s", category.id)
        return category

    def update_category(self, category, fields):
        for name, value in fields.items():
            setattr(category, name, value)
        self._session.commit()
        return category

    def delete_category(self, category_id):
        """Desassocia as tasks da categoria e a remove na mesma transação."""
        category = self.get_category(category_id)
        Task.detach_category(category_id)
        self._session.delete(category)
        self._session.commit()
        logger.info("Categoria deletada: id=%s", category_id)
