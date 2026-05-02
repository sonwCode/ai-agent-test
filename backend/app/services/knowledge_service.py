import re
from pathlib import Path
from typing import Iterable

from ..database import execute, query_all, query_one, utc_now
from ..settings import UPLOAD_DIR
from .audit_service import audit_service


STOPWORDS = {
    "的", "了", "和", "与", "及", "在", "为", "对", "是", "进行", "一个", "the", "and", "of", "to", "in", "a", "is",
}


def tokenize(text: str) -> list[str]:
    text = text.lower()
    words = re.findall(r"[a-zA-Z0-9_]{2,}|[\u4e00-\u9fff]", text)
    return [w for w in words if w not in STOPWORDS]


def chunk_text(text: str, max_chars: int = 850) -> list[str]:
    cleaned = re.sub(r"\r\n?", "\n", text).strip()
    if not cleaned:
        return []
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", cleaned) if p.strip()]
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_chars:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            if len(para) <= max_chars:
                current = para
            else:
                for i in range(0, len(para), max_chars):
                    chunks.append(para[i : i + max_chars])
                current = ""
    if current:
        chunks.append(current)
    return chunks


class KnowledgeService:
    def ingest_text(self, filename: str, content: str, raw_bytes: bytes | None = None) -> int:
        title = Path(filename).stem[:120] or "未命名资料"
        saved_path = ""
        if raw_bytes is not None:
            safe_name = re.sub(r"[^a-zA-Z0-9_.\-\u4e00-\u9fff]", "_", filename)
            saved = UPLOAD_DIR / f"{utc_now().replace(':', '-')}_{safe_name}"
            saved.write_bytes(raw_bytes)
            saved_path = str(saved)

        doc_id = execute(
            "INSERT INTO knowledge_docs(filename, title, content, file_path, created_at) VALUES (?, ?, ?, ?, ?)",
            (filename, title, content, saved_path, utc_now()),
        )

        chunks = chunk_text(content)
        for idx, chunk in enumerate(chunks):
            keywords = ",".join(sorted(set(tokenize(chunk)))[:80])
            execute(
                "INSERT INTO knowledge_chunks(doc_id, chunk_index, content, keywords, created_at) VALUES (?, ?, ?, ?, ?)",
                (doc_id, idx, chunk, keywords, utc_now()),
            )
        audit_service.log("knowledge.ingest", f"上传资料 {filename}，生成 {len(chunks)} 个知识片段")
        return doc_id

    def list_docs(self) -> list[dict]:
        rows = query_all(
            """
            SELECT d.id, d.filename, d.title, d.created_at, COUNT(c.id) AS chunk_count
            FROM knowledge_docs d
            LEFT JOIN knowledge_chunks c ON c.doc_id = d.id
            GROUP BY d.id
            ORDER BY d.id DESC
            """
        )
        return rows

    def search(self, query: str, limit: int = 6) -> list[dict]:
        q_tokens = tokenize(query)
        if not q_tokens:
            return []
        chunks = query_all(
            """
            SELECT c.id, c.doc_id, c.chunk_index, c.content, c.keywords, d.title, d.filename
            FROM knowledge_chunks c
            JOIN knowledge_docs d ON d.id = c.doc_id
            ORDER BY c.id DESC
            LIMIT 1000
            """
        )
        scored: list[tuple[float, dict]] = []
        for row in chunks:
            haystack = (row["content"] + " " + row["keywords"] + " " + row["title"]).lower()
            exact = sum(1 for t in q_tokens if t in haystack)
            overlap = len(set(q_tokens) & set(row["keywords"].split(",")))
            score = exact * 2.0 + overlap * 1.2
            if score > 0:
                item = dict(row)
                item["score"] = round(score, 2)
                scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]


knowledge_service = KnowledgeService()
