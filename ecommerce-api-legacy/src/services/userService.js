function createUserService({ db, users }) {
    return {
        // Mantém o comportamento original: matrículas e pagamentos são preservados
        // (histórico financeiro). Executa na fila de transações para não intercalar com um checkout.
        deleteUser(id) {
            return db.transaction(() => users.deleteById(id));
        },
    };
}

module.exports = { createUserService };
