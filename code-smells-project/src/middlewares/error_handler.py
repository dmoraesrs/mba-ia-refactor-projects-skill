"""Tratamento de erro centralizado: exceções de domínio viram JSON no formato original da API."""

import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        body = {"erro": error.message}
        if error.include_sucesso:
            body["sucesso"] = False
        return jsonify(body), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return error  # 404/405 de rota inexistente mantêm a resposta padrão do Flask

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
