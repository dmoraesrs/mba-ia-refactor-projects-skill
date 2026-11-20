"""Popula o banco com dados de exemplo (apaga os dados existentes).

As senhas dos usuários de exemplo vêm de SEED_PASSWORD; sem a variável, uma
senha aleatória é gerada e exibida uma única vez no log.
"""

import logging
import os
import secrets
from datetime import timedelta

from app import PROJECT_DIR, create_app
from dotenv import load_dotenv

from src.clock import utcnow_naive
from src.database import db
from src.models import Category, Task, User

logger = logging.getLogger("seed")

USERS = [
    {"name": "João Silva", "email": "joao@email.com", "role": "admin"},
    {"name": "Maria Santos", "email": "maria@email.com", "role": "user"},
    {"name": "Pedro Oliveira", "email": "pedro@email.com", "role": "manager"},
]

CATEGORIES = [
    {"name": "Backend", "description": "Tarefas de backend", "color": "#3498db"},
    {"name": "Frontend", "description": "Tarefas de frontend", "color": "#2ecc71"},
    {"name": "DevOps", "description": "Tarefas de infraestrutura", "color": "#e74c3c"},
    {"name": "Bug", "description": "Correção de bugs", "color": "#e67e22"},
]

# user/category são índices nas listas acima; due_in_days negativo = já vencida
TASKS = [
    {"title": "Implementar autenticação JWT", "description": "Adicionar autenticação real com JWT", "status": "pending", "priority": 1, "user": 0, "category": 0, "due_in_days": -3},
    {"title": "Criar tela de login", "description": "Tela de login responsiva", "status": "in_progress", "priority": 2, "user": 1, "category": 1, "due_in_days": 5},
    {"title": "Configurar CI/CD", "description": "Pipeline com GitHub Actions", "status": "done", "priority": 2, "user": 2, "category": 2, "tags": "devops,ci,github"},
    {"title": "Corrigir bug no filtro de busca", "description": "Filtro não funciona com caracteres especiais", "status": "pending", "priority": 1, "user": 0, "category": 3, "due_in_days": -1},
    {"title": "Adicionar paginação na API", "description": "Endpoints retornam todos os registros", "status": "pending", "priority": 3, "user": 0, "category": 0, "due_in_days": 10},
    {"title": "Escrever testes unitários", "description": "Cobertura mínima de 80%", "status": "pending", "priority": 2, "user": 1, "category": 0},
    {"title": "Documentar API com Swagger", "description": "Gerar documentação automática", "status": "cancelled", "priority": 4, "user": 2, "category": 0},
    {"title": "Refatorar models", "description": "Melhorar organização dos models", "status": "in_progress", "priority": 3, "user": 1, "category": 0, "tags": "refactor,tech-debt"},
    {"title": "Configurar monitoramento", "description": "Prometheus + Grafana", "status": "pending", "priority": 4, "user": 2, "category": 2, "due_in_days": 20},
    {"title": "Melhorar validações de input", "description": "Usar marshmallow ou pydantic", "status": "pending", "priority": 3, "user": 0, "category": 0, "tags": "improvement,validation"},
]


def seed_data(app, password):
    with app.app_context():
        db.session.execute(db.delete(Task))
        db.session.execute(db.delete(User))
        db.session.execute(db.delete(Category))

        users = []
        for data in USERS:
            user = User(**data)
            user.set_password(password)
            users.append(user)
        categories = [Category(**data) for data in CATEGORIES]
        db.session.add_all(users + categories)
        db.session.flush()

        now = utcnow_naive()
        for data in TASKS:
            due_in_days = data.get("due_in_days")
            db.session.add(Task(
                title=data["title"],
                description=data["description"],
                status=data["status"],
                priority=data["priority"],
                user_id=users[data["user"]].id,
                category_id=categories[data["category"]].id,
                due_date=now + timedelta(days=due_in_days) if due_in_days is not None else None,
                tags=data.get("tags"),
            ))
        db.session.commit()

        logger.info(
            "Seed concluído: %s usuários, %s categorias, %s tasks",
            User.count_all(), Category.count_all(), Task.count_all(),
        )


if __name__ == "__main__":
    load_dotenv(PROJECT_DIR / ".env")
    application = create_app()
    seed_password = os.environ.get("SEED_PASSWORD")
    if not seed_password:
        seed_password = secrets.token_urlsafe(12)
        logger.warning("SEED_PASSWORD não definido. Senha gerada para os usuários de exemplo: %s", seed_password)
    seed_data(application, seed_password)
