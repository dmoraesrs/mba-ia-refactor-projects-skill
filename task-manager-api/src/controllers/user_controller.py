"""Fluxo HTTP de usuários e login."""

from flask import jsonify, request

from src.constants import DEFAULT_ROLE
from src.controllers.validators import validate_login, validate_role, validate_user_create, validate_user_update


class UserController:
    def __init__(self, user_service, auth_service, authenticator):
        self._users = user_service
        self._auth = auth_service
        self._authenticator = authenticator

    def list_users(self):
        return jsonify(self._users.list_users()), 200

    def get_user(self, user_id):
        return jsonify(self._users.get_user_with_tasks(user_id)), 200

    def create_user(self):
        fields = validate_user_create(request.get_json())
        self._users.ensure_email_available(fields["email"])
        validate_role(fields["role"])
        if fields["role"] != DEFAULT_ROLE:
            self._authenticator.require_admin_user()  # só admin cria usuário com papel privilegiado
        user = self._users.create_user(fields)
        return jsonify(user.to_dict()), 201

    def update_user(self, user_id):
        user = self._users.get_user(user_id)
        fields = validate_user_update(request.get_json())
        if "role" in fields and fields["role"] != user.role:
            self._authenticator.require_admin_user()  # só admin muda papel
        user = self._users.update_user(user, fields)
        return jsonify(user.to_dict()), 200

    def delete_user(self, user_id):
        self._users.delete_user(user_id)
        return jsonify({"message": "Usuário deletado com sucesso"}), 200

    def list_user_tasks(self, user_id):
        return jsonify(self._users.list_user_tasks(user_id)), 200

    def login(self):
        email, password = validate_login(request.get_json())
        user, token = self._auth.login(email, password)
        return jsonify({"message": "Login realizado com sucesso", "user": user.to_dict(), "token": token}), 200
