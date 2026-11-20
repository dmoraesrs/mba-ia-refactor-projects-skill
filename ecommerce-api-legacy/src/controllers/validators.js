const { BadRequestError } = require('../errors');

const isNonEmptyString = (value) => typeof value === 'string' && value.length > 0;
const isPresentId = (value) => (typeof value === 'number' && value !== 0) || isNonEmptyString(value);

// Campos do contrato público: usr, eml, pwd, c_id, card.
function parseCheckoutInput(body) {
    const { usr, eml, pwd, c_id: courseId, card } = body || {};

    if (!isNonEmptyString(usr) || !isNonEmptyString(eml) || !isPresentId(courseId) || !isNonEmptyString(card)) {
        throw new BadRequestError();
    }
    if (pwd !== undefined && pwd !== null && typeof pwd !== 'string') {
        throw new BadRequestError();
    }

    return { name: usr, email: eml, password: pwd || null, courseId, cardNumber: card };
}

module.exports = { parseCheckoutInput };
