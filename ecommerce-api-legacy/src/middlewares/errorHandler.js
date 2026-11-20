const { AppError } = require('../errors');
const { Messages } = require('../constants');

const asyncHandler = (handler) => (req, res, next) =>
    Promise.resolve(handler(req, res, next)).catch(next);

function createErrorHandler({ logger }) {
    // eslint-disable-next-line no-unused-vars
    return function errorHandler(err, req, res, next) {
        if (err instanceof AppError) {
            return res.status(err.statusCode).send(err.message);
        }
        // Erros 4xx do próprio Express (ex.: JSON malformado no express.json) sem vazar stack.
        if (Number.isInteger(err.status) && err.status >= 400 && err.status < 500) {
            return res.status(err.status).send(Messages.BAD_REQUEST);
        }
        logger.error('Erro não tratado', { method: req.method, path: req.path, error: err.message });
        return res.status(500).send(Messages.INTERNAL_ERROR);
    };
}

module.exports = { asyncHandler, createErrorHandler };
