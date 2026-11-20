import logging

from flask import jsonify, request

from src.errors import ValidationError

logger = logging.getLogger(__name__)


class AdminController:
    def __init__(self, admin_model):
        self._admin = admin_model

    def reset_database(self):
        self._admin.apagar_tudo()
        logger.warning("Banco de dados resetado via /admin/reset-db")
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    def executar_query(self):
        dados = request.get_json(silent=True)
        query = dados.get("sql", "") if isinstance(dados, dict) else ""
        if not query or not isinstance(query, str):
            raise ValidationError("Query não informada")
        if not query.strip().upper().startswith("SELECT"):
            raise ValidationError("Apenas consultas SELECT são permitidas")
        return jsonify({"dados": self._admin.consultar_somente_leitura(query), "sucesso": True}), 200
