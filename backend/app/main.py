from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from .agents.orchestrator import orchestrator
from .database import init_db, query_all, query_one
from .schemas import Dashboard, KnowledgeDoc, TaskRunRequest
from .services.artifact_service import artifact_service
from .services.knowledge_service import knowledge_service
from .settings import BASE_DIR, settings

app = FastAPI(title=settings.app_name, version="1.0.0")

STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")

@app.on_event("startup")
def on_startup() -> None:
    init_db()
    _seed_demo_docs()


def _seed_demo_docs() -> None:
    existing = query_one("SELECT COUNT(*) AS c FROM knowledge_docs")
    if existing and existing["c"] > 0:
        return
    demo = """
企业运营中心周报制度

一、各业务小组每周五 18:00 前提交本周进展、核心指标、风险事项与下周计划。
二、周报必须包含关键数据口径说明，涉及客户信息时需要脱敏处理。
三、项目延期、预算异常、客户投诉等事项应进入风险跟踪清单，并明确责任人与处理时限。
四、对跨部门协作事项，需同步记录依赖部门、预计完成时间和阻塞原因。

客户服务工单处理规范

一、普通咨询类工单要求 24 小时内首次响应，复杂问题需说明预计处理时间。
二、涉及退款、合同、财务争议的工单必须升级给专人复核，不得由 AI 自动直接决策。
三、所有处理结论应保留证据链，包括客户描述、处理动作、引用制度和最终结论。
""".strip()
    knowledge_service.ingest_text("企业运营中心示例制度.md", demo, demo.encode("utf-8"))


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "llm_provider": settings.llm_provider}


@app.get("/api/dashboard", response_model=Dashboard)
def dashboard() -> dict:
    total_tasks = query_one("SELECT COUNT(*) AS c FROM agent_tasks")["c"]
    completed_tasks = query_one("SELECT COUNT(*) AS c FROM agent_tasks WHERE status = 'completed'")["c"]
    running_tasks = query_one("SELECT COUNT(*) AS c FROM agent_tasks WHERE status = 'running'")["c"]
    total_docs = query_one("SELECT COUNT(*) AS c FROM knowledge_docs")["c"]
    total_chunks = query_one("SELECT COUNT(*) AS c FROM knowledge_chunks")["c"]
    avg_row = query_one("SELECT COALESCE(AVG(quality_score), 0) AS v FROM agent_tasks WHERE status = 'completed'")
    recent_tasks = query_all("SELECT * FROM agent_tasks ORDER BY id DESC LIMIT 8")
    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "running_tasks": running_tasks,
        "total_docs": total_docs,
        "total_chunks": total_chunks,
        "avg_quality_score": round(float(avg_row["v"]), 1),
        "recent_tasks": recent_tasks,
    }


@app.post("/api/knowledge/upload")
async def upload_knowledge(file: UploadFile = File(...)) -> dict:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="文件为空")
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            content = raw.decode("gbk")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=400, detail="仅支持 UTF-8/GBK 文本文件，可先将 Word/PDF 内容复制为 txt/md。") from exc
    doc_id = knowledge_service.ingest_text(file.filename or "uploaded.txt", content, raw)
    return {"id": doc_id, "filename": file.filename, "message": "上传并切分完成"}


@app.get("/api/knowledge", response_model=list[KnowledgeDoc])
def list_knowledge() -> list[dict]:
    return knowledge_service.list_docs()


@app.post("/api/tasks/run")
def run_task(req: TaskRunRequest) -> dict:
    return orchestrator.run(req)


@app.get("/api/tasks")
def list_tasks() -> list[dict]:
    return orchestrator.list_tasks()


@app.get("/api/tasks/{task_id}")
def get_task(task_id: int) -> dict:
    task = orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@app.get("/api/artifacts/{artifact_id}", response_class=PlainTextResponse)
def get_artifact(artifact_id: int) -> str:
    artifact = artifact_service.get(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="生成物不存在")
    return artifact["content"]


@app.get("/api/artifacts/{artifact_id}/download")
def download_artifact(artifact_id: int) -> FileResponse:
    artifact = artifact_service.get(artifact_id)
    if not artifact or not artifact.get("file_path"):
        raise HTTPException(status_code=404, detail="生成物不存在")
    path = Path(artifact["file_path"])
    if not path.exists():
        path.write_text(artifact["content"], encoding="utf-8")
    return FileResponse(path, filename=path.name, media_type="text/markdown")
