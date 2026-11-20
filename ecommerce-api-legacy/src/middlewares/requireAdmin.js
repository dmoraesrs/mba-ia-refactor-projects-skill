const crypto = require('crypto');
const { UnauthorizedError } = require('../errors');

const digest = (value) => crypto.createHash('sha256').update(String(value)).digest();

// Exige "Authorization: Bearer <ADMIN_TOKEN>". Sem ADMIN_TOKEN configurado, as rotas ficam bloqueadas.
function createRequireAdmin({ adminToken }) {
    return function requireAdmin(req, res, next) {
        const header = req.get('authorization') || '';
        const provided = header.startsWith('Bearer ') ? header.slice('Bearer '.length) : '';
        if (!adminToken || !provided || !crypto.timingSafeEqual(digest(provided), digest(adminToken))) {
            return next(new UnauthorizedError());
        }
        return next();
    };
}

module.exports = { createRequireAdmin };
