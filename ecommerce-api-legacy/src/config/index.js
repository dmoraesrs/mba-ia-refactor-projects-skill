const DEFAULT_PORT = 3000;
const DEFAULT_DB_PATH = ':memory:';

function loadConfig(env = process.env) {
    return Object.freeze({
        port: Number(env.PORT || DEFAULT_PORT),
        dbPath: env.DB_PATH || DEFAULT_DB_PATH,
        paymentGatewayKey: env.PAYMENT_GATEWAY_KEY || '',
        adminToken: env.ADMIN_TOKEN || '',
        logLevel: env.LOG_LEVEL || 'info',
    });
}

module.exports = { loadConfig };
