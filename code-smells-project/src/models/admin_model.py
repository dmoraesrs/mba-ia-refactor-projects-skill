"""Operações administrativas de manutenção do banco."""

from contextlib import closing

_RESET_STATEMENTS = (
    "DELETE FROM itens_pedido",
    "DELETE FROM pedidos",
    "DELETE FROM produtos",
    "DELETE FROM usuarios",
)


class AdminModel:
    def __init__(self, database):
        self._db = database

    def apagar_tudo(self):
        connection = self._db.connection()
        with connection:
            for statement in _RESET_STATEMENTS:
                connection.execute(statement)

    def consultar_somente_leitura(self, sql):
        """Executa uma única consulta numa conexão read-only (mode=ro): escrita é impossível."""
        with closing(self._db.readonly_connection()) as connection:
            return [dict(row) for row in connection.execute(sql).fetchall()]
