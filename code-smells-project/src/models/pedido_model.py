"""Model de pedido e itens: escrita transacional e leitura sem N+1."""

from collections import defaultdict

from src.constants import PRODUTO_DESCONHECIDO, STATUS_APROVADO, STATUS_CANCELADO, STATUS_PENDENTE
from src.errors import BusinessRuleError

_SELECT_PEDIDOS = "SELECT id, usuario_id, status, total, criado_em FROM pedidos"
_SELECT_ITENS = (
    "SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario,"
    " p.id AS produto_existe, p.nome AS produto_nome"
    " FROM itens_pedido i LEFT JOIN produtos p ON p.id = i.produto_id"
)


def _item_to_dict(row):
    return {
        "produto_id": row["produto_id"],
        "produto_nome": row["produto_nome"] if row["produto_existe"] is not None else PRODUTO_DESCONHECIDO,
        "quantidade": row["quantidade"],
        "preco_unitario": row["preco_unitario"],
    }


def _pedido_to_dict(row, itens):
    return {
        "id": row["id"],
        "usuario_id": row["usuario_id"],
        "status": row["status"],
        "total": row["total"],
        "criado_em": row["criado_em"],
        "itens": itens,
    }


class PedidoModel:
    def __init__(self, database):
        self._db = database

    def criar(self, usuario_id, itens, total):
        """Grava pedido, itens e baixa de estoque numa única transação.

        `itens`: lista de dicts com produto_id, quantidade, preco_unitario e nome.
        A baixa é condicional (estoque >= quantidade); se falhar, tudo é desfeito.
        """
        connection = self._db.connection()
        with connection:
            pedido_id = connection.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, STATUS_PENDENTE, total),
            ).lastrowid
            for item in itens:
                connection.execute(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                    (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
                )
                baixa = connection.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                    (item["quantidade"], item["produto_id"], item["quantidade"]),
                )
                if baixa.rowcount == 0:
                    raise BusinessRuleError("Estoque insuficiente para " + item["nome"])
        return pedido_id

    def listar(self, usuario_id=None):
        connection = self._db.connection()
        if usuario_id is None:
            pedidos = connection.execute(_SELECT_PEDIDOS).fetchall()
            itens = connection.execute(_SELECT_ITENS + " ORDER BY i.id").fetchall()
        else:
            pedidos = connection.execute(_SELECT_PEDIDOS + " WHERE usuario_id = ?", (usuario_id,)).fetchall()
            itens = connection.execute(
                _SELECT_ITENS + " WHERE i.pedido_id IN (SELECT id FROM pedidos WHERE usuario_id = ?) ORDER BY i.id",  # noqa: S608 - só constantes do módulo e placeholders
                (usuario_id,),
            ).fetchall()

        itens_por_pedido = defaultdict(list)
        for item in itens:
            itens_por_pedido[item["pedido_id"]].append(_item_to_dict(item))
        return [_pedido_to_dict(row, itens_por_pedido[row["id"]]) for row in pedidos]

    def atualizar_status(self, pedido_id, status):
        connection = self._db.connection()
        with connection:
            connection.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))

    def resumo_vendas(self):
        row = self._db.connection().execute(
            "SELECT COUNT(*) AS total_pedidos,"
            " COALESCE(SUM(total), 0) AS faturamento,"
            " COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS pendentes,"
            " COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS aprovados,"
            " COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS cancelados"
            " FROM pedidos",
            (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
        ).fetchone()
        return dict(row)

    def contar(self):
        return self._db.connection().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
