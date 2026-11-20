"""Cadastro e autenticação de usuários com senha em hash."""

from src.models.usuario_model import usuario_to_login_dict
from src.security import hash_password, verify_password


class UsuarioService:
    def __init__(self, usuario_model):
        self._usuarios = usuario_model

    def criar(self, nome, email, senha):
        return self._usuarios.criar(nome, email, hash_password(senha))

    def autenticar(self, email, senha):
        row = self._usuarios.buscar_credenciais(email)
        if row is None or not verify_password(row["senha"], senha):
            return None
        return usuario_to_login_dict(row)
