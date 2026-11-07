# 快速开始：前后端工程初始化与启停脚本

## 目标

在本地完成依赖安装、配置模板准备、统一启动前端/后端/Celery，并验证最小联通链路。

工程结构与扩展边界见 [README.md](../../README.md)；脚本行为见 [scripts/README.md](../../scripts/README.md)；CLI 契约见 [contracts/devctl-cli.md](contracts/devctl-cli.md)。

## 前置条件

- 已安装 Python 3.11+
- 已安装 Node.js 20+ 与 `pnpm`
- 已安装 `uv`
- 当前分支为 `001-fullstack-bootstrap`

## 1. 初始化依赖

后端依赖：

```bash
cd server
uv sync
cp .env.example .env
```

说明：

- `server/.env.example` 只提供本地开发占位值，真实端口或路径变更需开发者自行调整。
- `.env` 缺失时，`./scripts/devctl.sh start` 会显式失败。

前端依赖：

```bash
cd ui
pnpm install
cp .env.example .env
```

说明：

- `ui/.env.example` 默认指向 `http://127.0.0.1:8000`。
- 如果后端端口调整，必须同步修改 `VITE_API_BASE_URL`。

## 2. 启动所有服务

```bash
./scripts/devctl.sh start
```

预期结果：

- 后端服务监听 `http://127.0.0.1:8000`
- 前端开发服务监听 `http://127.0.0.1:5173`（`vite.config.ts` 默认值；devctl 通过 `pnpm dev --port` 传入 `FRONTEND_PORT`，调整该值时以 `.env` 为准）
- Celery worker 成功启动并开始监听示例任务
- `devctl.sh` 仅在 backend/frontend 探针通过且 celery 进程保持存活后输出成功
- 日志文件生成在 `server/logs/`

## 3. 查看运行状态

```bash
./scripts/devctl.sh status
```

预期结果：

- `frontend`、`backend`、`celery` 都显示为 `running`
- 若有失败项，输出包含对应日志路径

## 4. 验证最小联通链路

后端健康检查：

```bash
curl http://127.0.0.1:8000/api/health
```

提交示例任务：

```bash
curl -X POST http://127.0.0.1:8000/api/dev/tasks/demo \
  -H "Content-Type: application/json" \
  -d '{"message":"bootstrap smoke"}'
```

查询任务状态：

```bash
curl http://127.0.0.1:8000/api/dev/tasks/<task_id>
```

前端验证：

- 打开 `http://127.0.0.1:5173`
- 页面应展示后端健康状态
- 页面可触发示例任务，并在“处理中”后轮询到 `SUCCESS` / `FAILURE` 或超时提示

## 5. 停止所有服务

```bash
./scripts/devctl.sh stop
```

预期结果：

- 3 个服务均停止
- `status` 再次执行后不再显示遗留运行进程

## 6. 日志排查

- 后端日志：`server/logs/backend.log`
- Celery 日志：`server/logs/celery.log`
- 前端日志：`server/logs/frontend.log`

如果启动失败：

- 先执行 `./scripts/devctl.sh status`
- 再查看对应日志文件
- 若为配置缺失，优先核对 `.env` 是否由模板正确补齐
- 若为重复启动、失效 PID 或端口冲突，脚本会直接输出责任服务和错误原因
- 若为启动后探针超时，脚本会自动停止已拉起服务，并提示对应日志路径
