const { PaymentStatus, UNKNOWN_STUDENT_NAME } = require('../constants');

function createReportService({ courses }) {
    return {
        async financialReport() {
            const rows = await courses.findAllWithEnrollments();
            const byCourse = new Map();

            for (const row of rows) {
                if (!byCourse.has(row.course_id)) {
                    byCourse.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
                }
                if (row.enrollment_id === null) continue;

                const entry = byCourse.get(row.course_id);
                if (row.payment_status === PaymentStatus.PAID) entry.revenue += row.payment_amount;
                entry.students.push({
                    student: row.student_name ?? UNKNOWN_STUDENT_NAME,
                    paid: row.payment_amount ?? 0,
                });
            }

            return [...byCourse.values()];
        },
    };
}

module.exports = { createReportService };
