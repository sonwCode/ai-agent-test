# Enterprise Agent Workbench

企业级 AI Agent 自动化工作台原型。它不是一个空壳聊天框，而是一个可运行的多 Agent 工作流系统：

- 需求理解 Agent：识别任务类型、目标、约束与交付格式
- 知识检索 Agent：从企业知识库召回资料与证据片段
- 结构化分析 Agent：整理背景、关键问题、指标、风险与建议
- 文档生成 Agent：生成周报、方案、会议纪要、运营分析等交付物
- 质量审核 Agent：检查事实依据、格式完整性、风险表述与可追溯性
- 流程编排器：记录任务状态、审计日志、Agent 执行轨迹与生成物

默认使用本地规则引擎模拟 LLM，保证没有 API Key 也能完整跑通。配置 OpenAI-compatible API 后，可替换为真实模型。

## 1. 技术栈

- Backend: Python 3.10+ / FastAPI / SQLite
- Frontend: 原生 HTML + CSS + JavaScript，无需 Node 环境
- Storage: SQLite + 本地文件目录
- Agent Runtime: 自研轻量编排器，支持状态流转、工具调用、审计日志、失败兜底

## 2. 快速启动

```bash
cd enterprise-agent-workbench
python -m venv .venv

# Windows PowerShell
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python run.py
```

启动后访问：

```text
http://127.0.0.1:8000
```

接口文档：

```text
http://127.0.0.1:8000/docs
```


## 2.1 上传到 GitHub

如果你已经在 GitHub 创建了 `https://github.com/sonwCode/ai-agent-test.git`，解压后不要只提交 README，而是在项目根目录提交全部文件：

```bash
cd enterprise-agent-workbench
git init
git add .
git commit -m "init: enterprise agent workbench"
git branch -M main
git remote add origin https://github.com/sonwCode/ai-agent-test.git
git push -u origin main
```

如果提示 `remote origin already exists`，用下面两行替代 `git remote add origin ...`：

```bash
git remote set-url origin https://github.com/sonwCode/ai-agent-test.git
git push -u origin main
```

如果远程仓库已经有 README，导致 push 被拒绝，可以先拉取合并：

```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

## 3. 可选：接入真实 OpenAI-compatible 模型

复制环境变量文件：

```bash
cp .env.example .env
```

填写：

```env
LLM_PROVIDER=openai-compatible
OPENAI_API_KEY=你的 API Key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
```

也可以配置 DeepSeek、智谱、硅基流动等兼容 OpenAI Chat Completions 协议的地址。

## 4. 演示流程

1. 打开首页
2. 上传若干企业制度、项目材料、运营报告或会议纪要 txt/md 文件
3. 在“创建 Agent 任务”中输入：
   - 标题：自动生成运营周报
   - 目标：基于已有资料，总结本周业务进展、风险和下周计划
   - 类型：运营周报
4. 点击“运行多 Agent 工作流”
5. 查看 Agent 执行链路、质量评分、生成物与审计日志

## 5. 目录结构

```text
enterprise-agent-workbench/
├─ backend/
│  └─ app/
│     ├─ agents/              # 多 Agent 实现
│     ├─ services/            # 知识库、审计、生成物服务
│     ├─ static/              # 前端页面
│     ├─ data/                # SQLite 与上传文件目录，运行时生成
│     ├─ database.py          # SQLite 初始化与访问封装
│     ├─ main.py              # FastAPI 应用入口
│     ├─ schemas.py           # Pydantic 请求/响应模型
│     └─ settings.py          # 配置读取
├─ tests/
│  └─ test_workflow.py
├─ .env.example
├─ Dockerfile
├─ docker-compose.yml
├─ requirements.txt
└─ run.py
```

## 6. 适合写进申请材料的项目描述

我参与建设了一个面向企业运营场景的 AI Agent 自动化工作平台，主要服务于内部知识检索、业务工单处理、经营数据分析、周报生成和方案初稿撰写等高频工作。平台采用多 Agent 协作模式，将复杂任务拆分为需求理解、知识检索、结构化分析、文档生成、流程执行和质量审核等环节，形成“任务识别—资料检索—工具调用—内容生成—自动校验—人工确认”的闭环。

在工程实现上，系统提供知识库上传、任务创建、Agent 执行轨迹、质量评分、审计日志和交付物下载等功能。通过流程编排器统一管理任务状态，保证每一步都有输入、输出和可追溯记录。该原型可用于演示企业内部知识管理、运营材料生成、会议纪要整理、周报自动化和业务分析辅助等场景。

## 7. 测试

```bash
pytest -q
```

通过测试后，说明健康检查接口、多 Agent 执行接口、质量评分和生成物链路均可运行。

## 8. Render 在线部署

Render 可直接读取本仓库。配置如下：

```text
Build Command: pip install -r requirements.txt
Start Command: uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

仓库中已包含 `render.yaml`，也可以按 Render 页面手动填写。

## 9. 注意

这是一个可运行的原型版本，重点是展示 Agent 工作流闭环和工程化能力。生产环境需要继续补充权限体系、向量数据库、企业单点登录、敏感信息脱敏、权限隔离、模型调用监控和成本管理。
