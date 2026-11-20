const { loadConfig } = require('./config');
const { createLogger } = require('./logger');
const { createApp } = require('./app');

const config = loadConfig();
const logger = createLogger(config.logLevel);

async function main() {
    if (!config.adminToken) logger.warn('ADMIN_TOKEN não definido: rotas administrativas responderão 401');
    if (!config.paymentGatewayKey) logger.warn('PAYMENT_GATEWAY_KEY não definido: gateway simulado sem chave');

    const { app } = await createApp({ config, logger });
    app.listen(config.port, () => logger.info(`LMS API rodando na porta ${config.port}`));
}

main().catch((err) => {
    logger.error('Falha ao iniciar a aplicação', { error: err.message });
    process.exit(1);
});
