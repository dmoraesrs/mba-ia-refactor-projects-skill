const { PaymentStatus, APPROVED_CARD_PREFIX } = require('../constants');

// Gateway simulado. Recebe a chave por injeção; nunca a registra em log.
function createPaymentGateway({ apiKey, logger }) {
    return {
        async charge({ cardNumber, amount }) {
            logger.info('Processando pagamento', { cardLast4: cardNumber.slice(-4), amount, keyConfigured: Boolean(apiKey) });
            return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PaymentStatus.PAID : PaymentStatus.DENIED;
        },
    };
}

module.exports = { createPaymentGateway };
