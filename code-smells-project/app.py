"""Entry point / composition root: cria a app, injeta dependências e registra rotas."""

import logging

from flask import Flask
from flask_cors import CORS

from src.config.settings import load_settings
from src.controllers.admin_controller import AdminController
from src.controllers.health_controller import HealthController
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.relatorio_controller import RelatorioController
from src.controllers.usuario_controller import UsuarioController
from src.database import Database
from src.middlewares.auth import build_admin_guard
from src.middlewares.error_handler import register_error_handlers
from src.models.admin_model import AdminModel
from src.models.pedido_model import PedidoModel
from src.models.produto_model import ProdutoModel
from src.models.usuario_model import UsuarioModel
from src.services.notification_service import LogNotificationService
from src.services.pedido_service import PedidoService
from src.services.relatorio_service import RelatorioService
from src.services.usuario_service import UsuarioService
from src.views.routes import build_blueprint

logger = logging.getLogger(__name__)


def create_app(settings=None):
    settings = settings or load_settings()
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    for name in settings.generated:
        logger.warning("%s não definido: usando valor aleatório válido só para este processo", name)
    if not settings.admin_token:
        logger.warning("ADMIN_TOKEN não definido: rotas /admin/* bloqueadas")

    app = Flask(__name__)
    app.config.update(SECRET_KEY=settings.secret_key, DEBUG=settings.debug)
    CORS(app, origins=settings.cors_origins)

    database = Database(settings.database_path)
    database.init_app(app)
    database.initialize(settings.seed_admin_password, settings.seed_customer_password)

    produto_model = ProdutoModel(database)
    usuario_model = UsuarioModel(database)
    pedido_model = PedidoModel(database)
    admin_model = AdminModel(database)

    pedido_service = PedidoService(pedido_model, produto_model, LogNotificationService())
    usuario_service = UsuarioService(usuario_model)
    relatorio_service = RelatorioService(pedido_model)

    controllers = {
        "produto": ProdutoController(produto_model),
        "usuario": UsuarioController(usuario_model, usuario_service),
        "pedido": PedidoController(pedido_service, pedido_model),
        "relatorio": RelatorioController(relatorio_service),
        "health": HealthController(produto_model, usuario_model, pedido_model, settings.app_env),
        "admin": AdminController(admin_model),
    }
    app.register_blueprint(build_blueprint(controllers, build_admin_guard(settings.admin_token)))
    register_error_handlers(app)
    return app


if __name__ == "__main__":
    settings = load_settings()
    application = create_app(settings)
    logger.info("Servidor iniciado em http://%s:%s", settings.host, settings.port)
    application.run(host=settings.host, port=settings.port, debug=settings.debug)
