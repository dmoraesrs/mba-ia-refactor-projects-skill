"""Instância do Flask-SQLAlchemy, ligada à app no composition root (db.init_app)."""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_database(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
