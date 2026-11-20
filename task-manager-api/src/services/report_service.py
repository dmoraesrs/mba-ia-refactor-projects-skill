"""Relatórios e estatísticas de tasks (agregações feitas no banco)."""

from datetime import timedelta

from src.clock import utcnow_naive
from src.constants import HIGH_PRIORITY_MAX, PRIORITY_LABELS, RECENT_ACTIVITY_DAYS, TASK_STATUSES
from src.errors import NotFoundError
from src.models import Category, Task, User


def completion_rate(done, total):
    return round((done / total) * 100, 2) if total > 0 else 0


class ReportService:
    def task_stats(self):
        by_status = Task.count_by_status()
        total = Task.count_all()
        done = by_status.get("done", 0)
        stats = {status: by_status.get(status, 0) for status in TASK_STATUSES}
        stats.update(
            total=total,
            overdue=len(Task.list_overdue(utcnow_naive())),
            completion_rate=completion_rate(done, total),
        )
        return stats

    def summary(self):
        now = utcnow_naive()
        by_status = Task.count_by_status()
        by_priority = Task.count_by_priority()
        overdue_tasks = Task.list_overdue(now)
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
        per_user = Task.count_by_user()

        user_productivity = []
        for user in User.list_all():
            total, completed = per_user.get(user.id, (0, 0))
            user_productivity.append({
                "user_id": user.id,
                "user_name": user.name,
                "total_tasks": total,
                "completed_tasks": completed,
                "completion_rate": completion_rate(completed, total),
            })

        return {
            "generated_at": str(now),
            "overview": {
                "total_tasks": Task.count_all(),
                "total_users": User.count_all(),
                "total_categories": Category.count_all(),
            },
            "tasks_by_status": {status: by_status.get(status, 0) for status in TASK_STATUSES},
            "tasks_by_priority": {label: by_priority.get(level, 0) for level, label in PRIORITY_LABELS.items()},
            "overdue": {
                "count": len(overdue_tasks),
                "tasks": [task.to_overdue_dict(now) for task in overdue_tasks],
            },
            "recent_activity": {
                "tasks_created_last_7_days": Task.count_created_since(since),
                "tasks_completed_last_7_days": Task.count_done_since(since),
            },
            "user_productivity": user_productivity,
        }

    def user_report(self, user_id):
        user = User.find_by_id(user_id)
        if not user:
            raise NotFoundError("Usuário não encontrado")

        now = utcnow_naive()
        tasks = Task.list_by_user(user_id)
        counts = {status: 0 for status in TASK_STATUSES}
        for task in tasks:
            if task.status in counts:
                counts[task.status] += 1
        total = len(tasks)

        return {
            "user": user.to_public_ref(),
            "statistics": {
                "total_tasks": total,
                **counts,
                "overdue": sum(1 for task in tasks if task.is_overdue(now)),
                "high_priority": sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_MAX),
                "completion_rate": completion_rate(counts["done"], total),
            },
        }
