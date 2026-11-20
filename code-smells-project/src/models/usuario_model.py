"""Model de usuário. A senha (hash) nunca sai na serialização pública."""

from src.constants import TIPO_CLIENTE

_COLUNAS_PUBLICAS = "id, nome, email, tipo, criado_em"


def usuario_to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def usuario_to_login_dict(row):
    return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}


class UsuarioModel:
    def __init__(self, database):
        self._db = database

    def listar(self):
        rows = self._db.connection().execute("SELECT " + _COLUNAS_PUBLICAS + " FROM usuarios").fetchall()  # noqa: S608 - só constantes do módulo e placeholders
        return [usuario_to_dict(row) for row in rows]

    def buscar_por_id(self, usuario_id):
        row = self._db.connection().execute(
            "SELECT " + _COLUNAS_PUBLICAS + " FROM usuarios WHERE id = ?", (usuario_id,)  # noqa: S608 - só constantes do módulo e placeholders
        ).fetchone()
        return usuario_to_dict(row) if row else None

    def buscar_credenciais(self, email):
        """Uso interno da autenticação: inclui o hash da senha."""
        return self._db.connection().execute(
            "SELECT id, nome, email, tipo, senha FROM usuarios WHERE email = ?", (email,)
        ).fetchone()

    def criar(self, nome, email, senha_hash, tipo=TIPO_CLIENTE):
        connection = self._db.connection()
        with connection:
            cursor = connection.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, senha_hash, tipo),
            )
        return cursor.lastrowid

    def contar(self):
        return self._db.connection().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
