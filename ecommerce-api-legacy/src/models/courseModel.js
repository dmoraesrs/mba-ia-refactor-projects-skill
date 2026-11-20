const { CourseStatus } = require('../constants');

function createCourseModel(db) {
    return {
        findActiveById(id) {
            return db.get('SELECT id, title, price FROM courses WHERE id = ? AND active = ?',
                [id, CourseStatus.ACTIVE]);
        },
        // Uma única query para o relatório (substitui o N+1): curso, matrícula, aluno e
        // o primeiro pagamento da matrícula (mesma semântica do db.get original).
        findAllWithEnrollments() {
            return db.all(`
                SELECT c.id AS course_id, c.title AS course_title,
                       e.id AS enrollment_id, u.name AS student_name,
                       p.amount AS payment_amount, p.status AS payment_status
                FROM courses c
                LEFT JOIN enrollments e ON e.course_id = c.id
                LEFT JOIN users u ON u.id = e.user_id
                LEFT JOIN payments p ON p.id = (
                    SELECT MIN(id) FROM payments WHERE enrollment_id = e.id
                )
                ORDER BY c.id, e.id`);
        },
    };
}

module.exports = { createCourseModel };
