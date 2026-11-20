"""Entidade Task, regra "atrasada" e consultas/agregações de tasks."""

from sqlalchemy import case, func, or_
from sqlalchemy.orm import joinedload

from src.clock import utcnow_naive
from src.constants import CLOSED_STATUSES, DEFAULT_PRIORITY, DEFAULT_TASK_STATUS, DONE_STATUS, TAGS_SEPARATOR
from src.database import db


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_TASK_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow_naive)
    updated_at = db.Column(db.DateTime, default=utcnow_naive, onupdate=utcnow_naive)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship("User", backref="tasks")
    category = db.relationship("Category", backref="tasks")

    # Regras da entidade ---------------------------------------------------
    def is_overdue(self, now=None):
        now = now or utcnow_naive()
        return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

    def days_overdue(self, now=None):
        now = now or utcnow_naive()
        return (now - self.due_date).days

    # Serialização ---------------------------------------------------------
    def to_dict(self, include_overdue=False, now=None):
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
            "due_date": self._due_date_str(),
            "tags": self.tags.split(TAGS_SEPARATOR) if self.tags else [],
        }
        if include_overdue:
            data["overdue"] = self.is_overdue(now)
        return data

    def to_list_dict(self, now=None):
        """Formato de GET /tasks: dados da task, atraso e nomes do usuário e da categoria."""
        data = self.to_dict(include_overdue=True, now=now)
        data["user_name"] = self.user.name if self.user else None
        data["category_name"] = self.category.name if self.category else None
        return data

    def to_summary_dict(self, now=None):
        """Formato de GET /users/<id>/tasks."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": str(self.created_at),
            "due_date": self._due_date_str(),
            "overdue": self.is_overdue(now),
        }

    def to_overdue_dict(self, now=None):
        return {
            "id": self.id,
            "title": self.title,
            "due_date": str(self.due_date),
            "days_overdue": self.days_overdue(now),
        }

    def _due_date_str(self):
        return str(self.due_date) if self.due_date else None

    # Consultas ------------------------------------------------------------
    @classmethod
    def find_by_id(cls, task_id):
        return db.session.get(cls, task_id)

    @classmethod
    def list_with_relations(cls):
        query = db.select(cls).options(joinedload(cls.user), joinedload(cls.category)).order_by(cls.id)
        return db.session.execute(query).scalars().all()

    @classmethod
    def list_by_user(cls, user_id):
        return db.session.execute(db.select(cls).where(cls.user_id == user_id).order_by(cls.id)).scalars().all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None):
        query = db.select(cls)
        if text:
            pattern = f"%{text}%"  # valor vinculado como parâmetro pelo ORM
            query = query.where(or_(cls.title.like(pattern), cls.description.like(pattern)))
        if status:
            query = query.where(cls.status == status)
        if priority is not None:
            query = query.where(cls.priority == priority)
        if user_id is not None:
            query = query.where(cls.user_id == user_id)
        return db.session.execute(query.order_by(cls.id)).scalars().all()

    @classmethod
    def list_overdue(cls, now):
        query = (
            db.select(cls)
            .where(cls.due_date.is_not(None), cls.due_date < now, cls.status.not_in(CLOSED_STATUSES))
            .order_by(cls.id)
        )
        return db.session.execute(query).scalars().all()

    @classmethod
    def count_all(cls):
        return db.session.execute(db.select(func.count(cls.id))).scalar_one()

    @classmethod
    def count_by_status(cls):
        rows = db.session.execute(db.select(cls.status, func.count(cls.id)).group_by(cls.status)).all()
        return dict(rows)

    @classmethod
    def count_by_priority(cls):
        rows = db.session.execute(db.select(cls.priority, func.count(cls.id)).group_by(cls.priority)).all()
        return dict(rows)

    @classmethod
    def count_by_user(cls):
        """{user_id: (total, concluídas)} numa única query."""
        done = func.sum(case((cls.status == DONE_STATUS, 1), else_=0))
        rows = db.session.execute(
            db.select(cls.user_id, func.count(cls.id), done).where(cls.user_id.is_not(None)).group_by(cls.user_id)
        ).all()
        return {user_id: (total, completed or 0) for user_id, total, completed in rows}

    @classmethod
    def count_by_category(cls):
        rows = db.session.execute(
            db.select(cls.category_id, func.count(cls.id)).where(cls.category_id.is_not(None)).group_by(cls.category_id)
        ).all()
        return dict(rows)

    @classmethod
    def count_created_since(cls, moment):
        return db.session.execute(db.select(func.count(cls.id)).where(cls.created_at >= moment)).scalar_one()

    @classmethod
    def count_done_since(cls, moment):
        query = db.select(func.count(cls.id)).where(cls.status == DONE_STATUS, cls.updated_at >= moment)
        return db.session.execute(query).scalar_one()

    @classmethod
    def delete_by_user(cls, user_id):
        db.session.execute(db.delete(cls).where(cls.user_id == user_id))

    @classmethod
    def detach_category(cls, category_id):
        db.session.execute(db.update(cls).where(cls.category_id == category_id).values(category_id=None))
