"""Exceções de domínio convertidas em resposta HTTP pelo error handler central."""


class AppError(Exception):
    status_code = 400
    include_sucesso = False

    def __init__(self, message, status_code=None, include_sucesso=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if include_sucesso is not None:
            self.include_sucesso = include_sucesso


class ValidationError(AppError):
    status_code = 400


class BusinessRuleError(AppError):
    """Regra de negócio violada (ex.: estoque insuficiente). Responde com "sucesso": false."""

    status_code = 400
    include_sucesso = True


class NotFoundError(AppError):
    status_code = 404


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403
