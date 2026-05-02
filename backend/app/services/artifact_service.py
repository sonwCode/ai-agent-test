import re
from pathlib import Path

from ..database import execute, query_one, utc_now
from ..settings import ARTIFACT_DIR


class ArtifactService:
    def create_markdown(self, task_id: int, name: str, content: str) -> int:
        safe_name = re.sub(r"[^a-zA-Z0-9_.\-\u4e00-\u9fff]", "_", name)[:80]
        file_path = ARTIFACT_DIR / f"task_{task_id}_{safe_name}.md"
        file_path.write_text(content, encoding="utf-8")
        return execute(
            "INSERT INTO artifacts(task_id, name, artifact_type, content, file_path, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (task_id, name, "markdown", content, str(file_path), utc_now()),
        )

    def get(self, artifact_id: int) -> dict | None:
        return query_one("SELECT * FROM artifacts WHERE id = ?", (artifact_id,))


artifact_service = ArtifactService()
