const LEVELS = { debug: 10, info: 20, warn: 30, error: 40, silent: 100 };

function createLogger(level = 'info') {
    const threshold = LEVELS[level] ?? LEVELS.info;
    const write = (name, stream) => (message, meta) => {
        if (LEVELS[name] < threshold) return;
        const line = `[${new Date().toISOString()}] ${name.toUpperCase()} ${message}`;
        stream(meta ? `${line} ${JSON.stringify(meta)}` : line);
    };
    return {
        debug: write('debug', console.log),
        info: write('info', console.log),
        warn: write('warn', console.error),
        error: write('error', console.error),
    };
}

module.exports = { createLogger };
