const PaymentStatus = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

const CourseStatus = Object.freeze({ ACTIVE: 1, INACTIVE: 0 });

// Regra do gateway simulado: cartões que começam com este prefixo são aprovados.
const APPROVED_CARD_PREFIX = '4';

const UNKNOWN_STUDENT_NAME = 'Unknown';

const Messages = Object.freeze({
    BAD_REQUEST: 'Bad Request',
    COURSE_NOT_FOUND: 'Curso não encontrado',
    PAYMENT_DENIED: 'Pagamento recusado',
    CHECKOUT_SUCCESS: 'Sucesso',
    USER_DELETED: 'Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.',
    UNAUTHORIZED: 'Não autorizado',
    INTERNAL_ERROR: 'Erro interno',
});

module.exports = { PaymentStatus, CourseStatus, APPROVED_CARD_PREFIX, UNKNOWN_STUDENT_NAME, Messages };
