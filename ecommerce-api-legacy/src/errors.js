const { Messages } = require('./constants');

class AppError extends Error {
    constructor(message, statusCode = 400) {
        super(message);
        this.name = this.constructor.name;
        this.statusCode = statusCode;
    }
}

class BadRequestError extends AppError {
    constructor(message = Messages.BAD_REQUEST) { super(message, 400); }
}

class NotFoundError extends AppError {
    constructor(message) { super(message, 404); }
}

class PaymentDeniedError extends AppError {
    constructor(message = Messages.PAYMENT_DENIED) { super(message, 400); }
}

class UnauthorizedError extends AppError {
    constructor(message = Messages.UNAUTHORIZED) { super(message, 401); }
}

module.exports = { AppError, BadRequestError, NotFoundError, PaymentDeniedError, UnauthorizedError };
