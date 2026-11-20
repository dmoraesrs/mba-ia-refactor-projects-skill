"""Entry point / composition root: cria a app, injeta dependências e registra rotas."""

import logging
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from src.config.settings import load_settings
from src.controllers.category_controller import CategoryController
from src.controllers.health_controller import HealthController
from src.controllers.report_controller import ReportController
from src.controllers.task_controller import TaskController
from src.controllers.user_controller import UserController
from src.database import db, init_database
from src.middlewares.auth import Authenticator
from src.middlewares.error_handler import register_error_handlers
from src.routes import register_routes
from src.security import TokenSigner
from src.services.auth_service import AuthService
from src.services.category_service import CategoryService
from src.services.notification_service import LogEmailSender, NotificationService, SmtpEmailSender
from src.services.report_service import ReportService
from src.services.task_service import TaskService
from src.services.user_service import UserService

PROJECT_DIR = Path(__file__).resolve().parent
logger = logging.getLogger(__name__)


def create_app(settings=None):
    if settings is None:
        load_dotenv(PROJECT_DIR / ".env")  # só o .env do projeto; variáveis já exportadas têm prioridade
        settings = load_settings()

    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    for name in settings.generated:
        logger.warning("%s não definido: usando valor aleatório válido só para este processo", name)

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.secret_key,
        SQLALCHEMY_DATABASE_URI=settings.database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        DEBUG=settings.debug,
    )
    CORS(app, origins=settings.cors_origins)
    init_database(app)

    email_sender = SmtpEmailSender(settings.smtp) if settings.smtp.enabled else LogEmailSender()
    notification_service = NotificationService(email_sender)
    auth_service = AuthService(db.session, TokenSigner(settings.secret_key, settings.token_max_age))
    report_service = ReportService()
    authenticator = Authenticator(auth_service)

    controllers = {
        "health": HealthController(),
        "task": TaskController(TaskService(db.session, notification_service), report_service),
        "user": UserController(UserService(db.session), auth_service, authenticator),
        "category": CategoryController(CategoryService(db.session)),
        "report": ReportController(report_service),
    }
    register_routes(app, controllers, authenticator)
    register_error_handlers(app)
    return app


if __name__ == "__main__":
    load_dotenv(PROJECT_DIR / ".env")
    settings = load_settings()
    application = create_app(settings)
    logger.info("Servidor iniciado em http://%s:%s", settings.host, settings.port)
    application.run(host=settings.host, port=settings.port, debug=settings.debug, load_dotenv=False)
