"""Rotas de status da API."""

from datetime import datetime

API_NAME = "Task Manager API"
API_VERSION = "1.0"


class HealthController:
    def index(self):
        return {"message": API_NAME, "version": API_VERSION}

    def health(self):
        return {"status": "ok", "timestamp": str(datetime.now())}
