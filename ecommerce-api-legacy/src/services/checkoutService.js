const { PaymentStatus, Messages } = require('../constants');
const { NotFoundError, PaymentDeniedError } = require('../errors');

function createCheckoutService({ db, users, courses, enrollments, payments, auditLogs, paymentGateway, passwordHasher }) {
    return {
        async checkout({ name, email, password, courseId, cardNumber }) {
            const course = await courses.findActiveById(courseId);
            if (!course) throw new NotFoundError(Messages.COURSE_NOT_FOUND);

            const status = await paymentGateway.charge({ cardNumber, amount: course.price });
            if (status !== PaymentStatus.PAID) throw new PaymentDeniedError();

            // Hash fora da transação para não segurar a fila durante o scrypt.
            const passwordHash = await passwordHasher.hash(password || passwordHasher.randomPassword());

            return db.transaction(async () => {
                const existing = await users.findByEmail(email);
                const userId = existing ? existing.id : await users.create({ name, email, passwordHash });
                const enrollmentId = await enrollments.create(userId, course.id);
                await payments.create(enrollmentId, course.price, status);
                await auditLogs.record(`Checkout curso ${course.id} por ${userId}`);
                return { enrollmentId };
            });
        },
    };
}

module.exports = { createCheckoutService };
