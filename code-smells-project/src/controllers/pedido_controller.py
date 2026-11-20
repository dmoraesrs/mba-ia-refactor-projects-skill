from flask import jsonify, request

from src.controllers.validators import extrair_status, validar_pedido


class PedidoController:
    def __init__(self, pedido_service, pedido_model):
        self._service = pedido_service
        self._pedidos = pedido_model

    def criar(self):
        dados = validar_pedido(request.get_json(silent=True))
        resultado = self._service.criar(dados["usuario_id"], dados["itens"])
        return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201

    def listar_todos(self):
        return jsonify({"dados": self._pedidos.listar(), "sucesso": True}), 200

    def listar_por_usuario(self, usuario_id):
        return jsonify({"dados": self._pedidos.listar(usuario_id), "sucesso": True}), 200

    def atualizar_status(self, pedido_id):
        self._service.atualizar_status(pedido_id, extrair_status(request.get_json(silent=True)))
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
