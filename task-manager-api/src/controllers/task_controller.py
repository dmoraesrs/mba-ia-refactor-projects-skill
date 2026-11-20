"""Fluxo HTTP de tasks: lê a requisição, valida, chama o service e monta a resposta."""

from flask import jsonify, request

from src.controllers.validators import parse_search_filters, validate_task_create, validate_task_update


class TaskController:
    def __init__(self, task_service, report_service):
        self._tasks = task_service
        self._reports = report_service

    def list_tasks(self):
        return jsonify(self._tasks.list_tasks()), 200

    def get_task(self, task_id):
        task = self._tasks.get_task(task_id)
        return jsonify(task.to_dict(include_overdue=True)), 200

    def create_task(self):
        fields = validate_task_create(request.get_json())
        task = self._tasks.create_task(fields)
        return jsonify(task.to_dict()), 201

    def update_task(self, task_id):
        task = self._tasks.get_task(task_id)
        fields = validate_task_update(request.get_json())
        task = self._tasks.update_task(task, fields)
        return jsonify(task.to_dict()), 200

    def delete_task(self, task_id):
        self._tasks.delete_task(task_id)
        return jsonify({"message": "Task deletada com sucesso"}), 200

    def search_tasks(self):
        return jsonify(self._tasks.search(parse_search_filters(request.args))), 200

    def task_stats(self):
        return jsonify(self._reports.task_stats()), 200
