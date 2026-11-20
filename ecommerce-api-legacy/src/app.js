const express = require('express');
const { openDatabase } = require('./database/connection');
const { initSchema } = require('./database/schema');
const { createUserModel } = require('./models/userModel');
const { createCourseModel } = require('./models/courseModel');
const { createEnrollmentModel } = require('./models/enrollmentModel');
const { createPaymentModel } = require('./models/paymentModel');
const { createAuditLogModel } = require('./models/auditLogModel');
const { createPasswordHasher } = require('./services/passwordHasher');
const { createPaymentGateway } = require('./services/paymentGateway');
const { createCheckoutService } = require('./services/checkoutService');
const { createReportService } = require('./services/reportService');
const { createUserService } = require('./services/userService');
const { createCheckoutController } = require('./controllers/checkoutController');
const { createReportController } = require('./controllers/reportController');
const { createUserController } = require('./controllers/userController');
const { createRequireAdmin } = require('./middlewares/requireAdmin');
const { createErrorHandler } = require('./middlewares/errorHandler');
const { buildRoutes } = require('./routes');

// Composition root: cria as dependências uma vez e injeta em cada camada.
async function createApp({ config, logger }) {
    const db = openDatabase(config.dbPath);
    const passwordHasher = createPasswordHasher();
    await initSchema(db, { passwordHasher });

    const users = createUserModel(db);
    const courses = createCourseModel(db);
    const enrollments = createEnrollmentModel(db);
    const payments = createPaymentModel(db);
    const auditLogs = createAuditLogModel(db);

    const paymentGateway = createPaymentGateway({ apiKey: config.paymentGatewayKey, logger });
    const checkoutService = createCheckoutService({
        db, users, courses, enrollments, payments, auditLogs, paymentGateway, passwordHasher,
    });
    const reportService = createReportService({ courses });
    const userService = createUserService({ db, users });

    const app = express();
    app.use(express.json());
    app.use(buildRoutes({
        checkoutController: createCheckoutController({ checkoutService }),
        reportController: createReportController({ reportService }),
        userController: createUserController({ userService }),
        requireAdmin: createRequireAdmin({ adminToken: config.adminToken }),
    }));
    app.use(createErrorHandler({ logger }));

    return { app, db };
}

module.exports = { createApp };
