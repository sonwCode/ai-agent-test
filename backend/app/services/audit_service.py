from ..database import execute, utc_now


class AuditService:
    def log(self, action: str, detail: str, task_id: int | None = None) -> None:
        execute(
            "INSERT INTO audit_logs(task_id, action, detail, created_at) VALUES (?, ?, ?, ?)",
            (task_id, action, detail, utc_now()),
        )


audit_service = AuditService()
