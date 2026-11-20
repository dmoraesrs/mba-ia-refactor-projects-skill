"""Notificações de tasks. O transporte (log ou SMTP) é injetado pelo composition root."""

import logging
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


class LogEmailSender:
    """Transporte padrão quando o SMTP não está configurado: só registra no log."""

    def send(self, to, subject, body):
        logger.info("E-mail não enviado (SMTP não configurado): assunto=%r", subject)
        return True


class SmtpEmailSender:
    def __init__(self, smtp_settings):
        self._settings = smtp_settings

    def send(self, to, subject, body):
        message = EmailMessage()
        message["From"] = self._settings.sender
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        try:
            with smtplib.SMTP(self._settings.host, self._settings.port, timeout=10) as server:
                server.starttls()
                server.login(self._settings.user, self._settings.password)
                server.send_message(message)
        except (smtplib.SMTPException, OSError):
            # Falha de notificação não pode desfazer a operação principal: registra e segue.
            logger.exception("Falha ao enviar e-mail de notificação")
            return False
        logger.info("E-mail de notificação enviado: assunto=%r", subject)
        return True


class NotificationService:
    def __init__(self, email_sender):
        self._sender = email_sender

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        return self._sender.send(user.email, subject, body)
