from dataclasses import dataclass
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatuIcons(Enum):
    PENDING = "[ ]"
    IN_PROGRESS = "[~]"
    COMPLETED = "[x]"
    FAILED = "[!]"


@dataclass
class Task:
    id: str
    description: str
    status: str = TaskStatus.PENDING.value


class TaskManager:
    def __init__(self):
        self._tasks: list[Task] = []
        self._next_id: int = 1

    def create(self, description: str) -> str:
        task_id = f"task_{self._next_id}"
        self._next_id += 1
        self._tasks.append(Task(id=task_id, description=description))
        return task_id

    def update(self, task_id: str, status: str | TaskStatus) -> bool:
        normalized_status = self._normalize_status(status)
        if normalized_status is None:
            return False

        for task in self._tasks:
            if task.id == task_id:
                task.status = normalized_status
                return True
        return False

    def get(self, task_id: str) -> Task | None:
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def list(self, status: str | TaskStatus | None = None) -> list[Task]:
        if status is None:
            return list(self._tasks)

        normalized_status = self._normalize_status(status)
        if normalized_status is None:
            return []

        return [task for task in self._tasks if task.status == normalized_status]

    def clear(self) -> None:
        self._tasks = []
        self._next_id = 1

    def format_for_llm(self) -> str:
        if not self._tasks:
            return "(no tasks)"

        lines: list[str] = []
        for task in self._tasks:
            icon = TaskStatuIcons[task.status.upper()].value
            lines.append(f"{icon} {task.id}: {task.description}")

        return "\n".join(lines)

    def format_task_list(self) -> str:
        return self.format_for_llm()

    @staticmethod
    def _normalize_status(status: str | TaskStatus) -> str | None:
        if isinstance(status, TaskStatus):
            return status.value

        if not isinstance(status, str):
            return None

        normalized = status.strip().lower()
        if normalized in {item.value for item in TaskStatus}:
            return normalized

        return None


    @property
    def length(self) -> int:
        return len(self._tasks)
