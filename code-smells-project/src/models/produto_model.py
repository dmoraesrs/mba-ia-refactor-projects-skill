"""Model de produto: queries parametrizadas e serialização única."""

_COLUNAS = "id, nome, descricao, preco, estoque, categoria, ativo, criado_em"


def produto_to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


class ProdutoModel:
    def __init__(self, database):
        self._db = database

    def listar(self):
        rows = self._db.connection().execute("SELECT " + _COLUNAS + " FROM produtos").fetchall()  # noqa: S608 - só constantes do módulo e placeholders
        return [produto_to_dict(row) for row in rows]

    def buscar_por_id(self, produto_id):
        row = self._db.connection().execute(
            "SELECT " + _COLUNAS + " FROM produtos WHERE id = ?", (produto_id,)  # noqa: S608 - só constantes do módulo e placeholders
        ).fetchone()
        return produto_to_dict(row) if row else None

    def buscar_por_ids(self, produto_ids):
        """Carrega vários produtos numa única query; devolve {id: produto}."""
        ids = list(dict.fromkeys(produto_ids))
        if not ids:
            return {}
        placeholders = ",".join("?" * len(ids))
        rows = self._db.connection().execute(
            "SELECT " + _COLUNAS + " FROM produtos WHERE id IN (" + placeholders + ")", ids  # noqa: S608 - só constantes do módulo e placeholders
        ).fetchall()
        return {row["id"]: produto_to_dict(row) for row in rows}

    def criar(self, nome, descricao, preco, estoque, categoria):
        connection = self._db.connection()
        with connection:
            cursor = connection.execute(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                (nome, descricao, preco, estoque, categoria),
            )
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        connection = self._db.connection()
        with connection:
            connection.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
                (nome, descricao, preco, estoque, categoria, produto_id),
            )

    def deletar(self, produto_id):
        connection = self._db.connection()
        with connection:
            connection.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))

    def pesquisar(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        clauses, params = [], []
        if termo:
            clauses.append("(nome LIKE ? OR descricao LIKE ?)")
            params.extend(["%" + termo + "%", "%" + termo + "%"])
        if categoria:
            clauses.append("categoria = ?")
            params.append(categoria)
        if preco_min:
            clauses.append("preco >= ?")
            params.append(preco_min)
        if preco_max:
            clauses.append("preco <= ?")
            params.append(preco_max)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = self._db.connection().execute("SELECT " + _COLUNAS + " FROM produtos" + where, params).fetchall()  # noqa: S608 - só constantes do módulo e placeholders
        return [produto_to_dict(row) for row in rows]

    def contar(self):
        return self._db.connection().execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
