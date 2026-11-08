# my_pro：前后端工程初始化与启停脚本

本地开发骨架：FastAPI 后端 + Celery worker（文件系统 broker / PostgreSQL（pgvector）结果存储）+ Vite/React 前端，由统一脚本 `scripts/devctl.sh` 管理启停。

## 快速开始

前置条件：Python 3.11+、Node.js 20+ 与 `pnpm`、`uv`。

```bash
cd server && uv sync && cp .env.example .env
docker compose -f docker/docker-compose.dev.yml up -d postgres
uv run python scripts/migrate_postgres_schema.py
cd ../ui && pnpm install && cp .env.example .env
./scripts/devctl.sh start
```

完整步骤与最小联通验证见 [specs/001-fullstack-bootstrap/quickstart.md](specs/001-fullstack-bootstrap/quickstart.md)。

## 目录结构

```
my_pro/
├── scripts/            # 统一启停脚本 devctl.sh（见 scripts/README.md）
├── server/             # FastAPI 后端，分层架构（见 server/README.md）
│   ├── src/            # core / domain / application / infrastructure / presentation
│   ├── tests/          # contract / integration / unit 测试
│   ├── logs/           # 运行日志（devctl 写入，不入库）
│   └── .runtime/       # PID、Celery 队列（不入库）
├── ui/                 # Vite + React + Tailwind 前端（见 ui/README.md）
└── specs/              # 规格、契约与快速开始文档
```

三个入口：

| 入口 | 位置 | 启动命令 |
|---|---|---|
| 后端 | `server/src/main.py` | `uv run uvicorn src.main:app` |
| Celery | `server/src/celery_app.py` | `uv run celery -A src.celery_app:app worker` |
| 前端 | `ui/src/main.tsx` | `pnpm dev` |

## 扩展边界

- 后端新增代码按层放置：业务规则 → `server/src/domain/`，用例编排 → `server/src/application/`，外部依赖（broker、存储、日志实现）→ `server/src/infrastructure/`，HTTP 路由 → `server/src/presentation/api/`。详见 [server/src/README.md](server/src/README.md)。
- 前端新增功能按 feature 目录放置（如 `ui/src/features/<feature>/`），跨 feature 复用的组件与工具放 `ui/src/shared/`。详见 [ui/README.md](ui/README.md)。

## 配置与日志

- 配置模板：`server/.env.example`、`ui/.env.example`；真实 `.env` 由开发者本地生成，不入库。
- 日志目录：`server/logs/`（`backend.log`、`celery.log`、`frontend.log`）。
- 运行状态：`server/.runtime/`（PID 文件、Celery 文件系统队列）。

## 持久化

- 运行时持久化为 PostgreSQL（pgvector）：`DATABASE_URL` 必填；`docker/docker-compose.dev.yml` 启动 pgvector PostgreSQL 服务。
- 旧 SQLite 数据文件不迁移、不读取。
- Schema 初始化命令：`cd server && uv run python scripts/migrate_postgres_schema.py`（幂等），校验输出包含 `vector_extension: true`。

## 验证

```bash
cd server && pytest
```

验收口径与故障排查见 [quickstart.md](specs/001-fullstack-bootstrap/quickstart.md)；CLI 契约见 [contracts/devctl-cli.md](specs/001-fullstack-bootstrap/contracts/devctl-cli.md)。
