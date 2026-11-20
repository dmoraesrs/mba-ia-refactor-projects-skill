"""Tratamento de erro centralizado: exceções de domínio viram JSON {"error": ...} como na API original."""

import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.database import db
from src.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        db.session.rollback()
        return jsonify({"error": error.message}), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return error  # 404/405/415 do próprio Flask mantêm a resposta padrão

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        db.session.rollback()
        logger.exception("Erro não tratado")
        return jsonify({"error": "Erro interno"}), 500
