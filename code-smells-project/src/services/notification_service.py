"""Notificações de pedido. Implementação atual: registra no log (gateway real pode substituir)."""

import logging

from src.constants import STATUS_APROVADO, STATUS_CANCELADO

logger = logging.getLogger(__name__)


class LogNotificationService:
    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("Notificação (email/sms/push): pedido %s criado para usuário %s", pedido_id, usuario_id)

    def status_alterado(self, pedido_id, status):
        if status == STATUS_APROVADO:
            logger.info("Notificação: pedido %s aprovado, preparar envio", pedido_id)
        elif status == STATUS_CANCELADO:
            logger.info("Notificação: pedido %s cancelado, devolver estoque", pedido_id)
