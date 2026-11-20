"""Entidade User e consultas de usuários."""

from src.clock import utcnow_naive
from src.constants import ADMIN_ROLE, DEFAULT_ROLE
from src.database import db
from src.security import hash_password, is_legacy_hash, verify_password


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # guarda o hash, nunca serializado
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow_naive)

    # Serialização ---------------------------------------------------------
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "active": self.active,
            "created_at": str(self.created_at),
        }

    def to_public_ref(self):
        return {"id": self.id, "name": self.name, "email": self.email}

    # Regras da entidade ---------------------------------------------------
    def set_password(self, raw_password):
        self.password = hash_password(raw_password)

    def check_password(self, raw_password):
        return verify_password(self.password, raw_password)

    def has_legacy_password_hash(self):
        return is_legacy_hash(self.password)

    def is_admin(self):
        return self.role == ADMIN_ROLE

    # Consultas ------------------------------------------------------------
    @classmethod
    def find_by_id(cls, user_id):
        return db.session.get(cls, user_id)

    @classmethod
    def find_by_email(cls, email):
        return db.session.execute(db.select(cls).where(cls.email == email)).scalar_one_or_none()

    @classmethod
    def list_all(cls):
        return db.session.execute(db.select(cls).order_by(cls.id)).scalars().all()

    @classmethod
    def count_all(cls):
        return db.session.execute(db.select(db.func.count(cls.id))).scalar_one()
