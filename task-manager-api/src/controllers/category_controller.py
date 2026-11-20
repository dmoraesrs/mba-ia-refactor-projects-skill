"""Fluxo HTTP de categorias."""

from flask import jsonify, request

from src.controllers.validators import validate_category_create, validate_category_update


class CategoryController:
    def __init__(self, category_service):
        self._categories = category_service

    def list_categories(self):
        return jsonify(self._categories.list_categories()), 200

    def create_category(self):
        category = self._categories.create_category(validate_category_create(request.get_json()))
        return jsonify(category.to_dict()), 201

    def update_category(self, category_id):
        category = self._categories.get_category(category_id)
        fields = validate_category_update(request.get_json())
        category = self._categories.update_category(category, fields)
        return jsonify(category.to_dict()), 200

    def delete_category(self, category_id):
        self._categories.delete_category(category_id)
        return jsonify({"message": "Categoria deletada"}), 200
