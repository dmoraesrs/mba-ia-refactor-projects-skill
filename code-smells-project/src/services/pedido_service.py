"""Caso de uso de pedidos: valida estoque, calcula total, persiste e notifica."""

from src.constants import STATUS_PEDIDO
from src.errors import BusinessRuleError, ValidationError


class PedidoService:
    def __init__(self, pedido_model, produto_model, notifier):
        self._pedidos = pedido_model
        self._produtos = produto_model
        self._notifier = notifier

    def criar(self, usuario_id, itens):
        produtos = self._produtos.buscar_por_ids(item["produto_id"] for item in itens)

        total = 0
        linhas = []
        for item in itens:
            produto = produtos.get(item["produto_id"])
            if produto is None:
                raise BusinessRuleError("Produto " + str(item["produto_id"]) + " não encontrado")
            if produto["estoque"] < item["quantidade"]:
                raise BusinessRuleError("Estoque insuficiente para " + produto["nome"])
            total = total + (produto["preco"] * item["quantidade"])
            linhas.append({
                "produto_id": item["produto_id"],
                "quantidade": item["quantidade"],
                "preco_unitario": produto["preco"],
                "nome": produto["nome"],
            })

        pedido_id = self._pedidos.criar(usuario_id, linhas, total)
        self._notifier.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def atualizar_status(self, pedido_id, status):
        if status not in STATUS_PEDIDO:
            raise ValidationError("Status inválido")
        self._pedidos.atualizar_status(pedido_id, status)
        self._notifier.status_alterado(pedido_id, status)
