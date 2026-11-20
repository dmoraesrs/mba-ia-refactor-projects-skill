"""Constantes de negócio usadas por validators, models e services."""

import re

# Tasks
TASK_STATUSES = ("pending", "in_progress", "done", "cancelled")
DEFAULT_TASK_STATUS = "pending"
DONE_STATUS = "done"
CLOSED_STATUSES = ("done", "cancelled")  # tasks fechadas nunca ficam atrasadas

TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 200

PRIORITY_MIN = 1
PRIORITY_MAX = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_MAX = 2  # prioridades 1 e 2 contam como "alta prioridade" no relatório do usuário
PRIORITY_LABELS = {1: "critical", 2: "high", 3: "medium", 4: "low", 5: "minimal"}

DUE_DATE_FORMAT = "%Y-%m-%d"
TAGS_SEPARATOR = ","

# Users
USER_ROLES = ("user", "admin", "manager")
DEFAULT_ROLE = "user"
ADMIN_ROLE = "admin"
MIN_PASSWORD_LENGTH = 4
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")

# Categories
DEFAULT_CATEGORY_COLOR = "#000000"
COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")

# Relatórios
RECENT_ACTIVITY_DAYS = 7
