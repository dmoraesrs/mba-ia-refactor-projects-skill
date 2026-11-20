import logging

from flask import jsonify, request

from src.controllers.validators import validar_filtros_busca, validar_produto
from src.errors import NotFoundError

logger = logging.getLogger(__name__)


class ProdutoController:
    def __init__(self, produto_model):
        self._produtos = produto_model

    def listar(self):
        produtos = self._produtos.listar()
        logger.debug("Listando %d produtos", len(produtos))
        return jsonify({"dados": produtos, "sucesso": True}), 200

    def buscar(self, produto_id):
        produto = self._produtos.buscar_por_id(produto_id)
        if not produto:
            raise NotFoundError("Produto não encontrado", include_sucesso=True)
        return jsonify({"dados": produto, "sucesso": True}), 200

    def pesquisar(self):
        filtros = validar_filtros_busca(request.args)
        resultados = self._produtos.pesquisar(**filtros)
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200

    def criar(self):
        produto = validar_produto(request.get_json(silent=True))
        produto_id = self._produtos.criar(**produto)
        logger.info("Produto criado com ID %s", produto_id)
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    def atualizar(self, produto_id):
        if not self._produtos.buscar_por_id(produto_id):
            raise NotFoundError("Produto não encontrado")
        produto = validar_produto(request.get_json(silent=True))
        self._produtos.atualizar(produto_id, **produto)
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def deletar(self, produto_id):
        if not self._produtos.buscar_por_id(produto_id):
            raise NotFoundError("Produto não encontrado")
        self._produtos.deletar(produto_id)
        logger.info("Produto %s deletado", produto_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
