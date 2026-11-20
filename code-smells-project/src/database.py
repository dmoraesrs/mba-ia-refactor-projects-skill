"""Acesso ao SQLite: conexão por requisição, schema e seed."""

import logging
import sqlite3
from contextlib import closing
from pathlib import Path

from flask import g

from src.constants import TIPO_ADMIN, TIPO_CLIENTE
from src.security import hash_password, is_hashed

logger = logging.getLogger(__name__)

_SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        descricao TEXT,
        preco REAL,
        estoque INTEGER,
        categoria TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        senha TEXT,
        tipo TEXT DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        status TEXT DEFAULT 'pendente',
        total REAL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        produto_id INTEGER,
        quantidade INTEGER,
        preco_unitario REAL
    )
    """,
)

_SEED_PRODUTOS = [
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
]


class Database:
    """Abre uma conexão SQLite por requisição (flask.g) em vez de uma global compartilhada."""

    _G_KEY = "db_connection"

    def __init__(self, path):
        self._path = path

    def init_app(self, app):
        app.teardown_appcontext(self._close)

    def _open(self):
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection

    def connection(self):
        if self._G_KEY not in g:
            setattr(g, self._G_KEY, self._open())
        return getattr(g, self._G_KEY)

    def readonly_connection(self):
        """Conexão nova somente leitura; o chamador deve fechá-la."""
        uri = Path(self._path).resolve().as_uri() + "?mode=ro"
        connection = sqlite3.connect(uri, uri=True)
        connection.row_factory = sqlite3.Row
        return connection

    def _close(self, _exc):
        connection = g.pop(self._G_KEY, None)
        if connection is not None:
            connection.close()

    def initialize(self, seed_admin_password, seed_customer_password):
        """Cria o schema, faz o seed inicial e migra senhas antigas em texto puro para hash."""
        with closing(self._open()) as connection, connection:
            for statement in _SCHEMA:
                connection.execute(statement)

            if connection.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 0:
                connection.executemany(
                    "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                    _SEED_PRODUTOS,
                )
                connection.executemany(
                    "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                    [
                        ("Admin", "admin@loja.com", hash_password(seed_admin_password), TIPO_ADMIN),
                        ("João Silva", "joao@email.com", hash_password(seed_customer_password), TIPO_CLIENTE),
                        ("Maria Santos", "maria@email.com", hash_password(seed_customer_password), TIPO_CLIENTE),
                    ],
                )
                logger.info("Banco inicializado com dados de exemplo")

            legado = [
                (hash_password(row["senha"]), row["id"])
                for row in connection.execute("SELECT id, senha FROM usuarios")
                if row["senha"] and not is_hashed(row["senha"])
            ]
            if legado:
                connection.executemany("UPDATE usuarios SET senha = ? WHERE id = ?", legado)
                logger.warning("%d senha(s) em texto puro migrada(s) para hash", len(legado))
