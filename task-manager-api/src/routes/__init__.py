"""Camada View da API: cada módulo só mapeia URL + método para um controller."""

from src.routes.category_routes import build_category_blueprint
from src.routes.health_routes import build_health_blueprint
from src.routes.report_routes import build_report_blueprint
from src.routes.task_routes import build_task_blueprint
from src.routes.user_routes import build_user_blueprint


def register_routes(app, controllers, authenticator):
    app.register_blueprint(build_health_blueprint(controllers["health"]))
    app.register_blueprint(build_task_blueprint(controllers["task"], authenticator))
    app.register_blueprint(build_user_blueprint(controllers["user"], authenticator))
    app.register_blueprint(build_category_blueprint(controllers["category"], authenticator))
    app.register_blueprint(build_report_blueprint(controllers["report"]))
