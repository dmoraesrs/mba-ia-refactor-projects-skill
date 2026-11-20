import logging
import sqlite3

from flask import jsonify

from src.constants import APP_VERSION

logger = logging.getLogger(__name__)


class HealthController:
    def __init__(self, produto_model, usuario_model, pedido_model, app_env):
        self._produtos = produto_model
        self._usuarios = usuario_model
        self._pedidos = pedido_model
        self._app_env = app_env

    def index(self):
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": APP_VERSION,
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        })

    def health(self):
        try:
            counts = {
                "produtos": self._produtos.contar(),
                "usuarios": self._usuarios.contar(),
                "pedidos": self._pedidos.contar(),
            }
        except sqlite3.Error:
            logger.exception("Health check falhou ao consultar o banco")
            return jsonify({"status": "erro", "detalhes": "Banco de dados indisponível"}), 500
        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": counts,
            "versao": APP_VERSION,
            "ambiente": self._app_env,
        }), 200
