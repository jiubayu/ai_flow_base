# scripts/devctl.sh

统一启停入口，管理 `backend`、`celery`、`frontend` 三个本地服务。

```bash
./scripts/devctl.sh <start|stop|status>
```

## 子命令

- `start`：依次启动三个服务；每个服务先做前置检查（配置完整、端口可用、无重复运行），启动后 backend/frontend 走健康探针、celery 检查进程存活。任一失败会清理本次已拉起的服务并输出责任服务与日志路径。
- `stop`：停止由 devctl 记录的服务；PID 失效时显式提示并清理 PID 文件。
- `status`：逐服务输出 `service / state / pid / log_path / message`，状态为 `running` / `stopped` / `failed`。

## 前置条件

- `server/.env` 存在且必填项完整（从 `server/.env.example` 复制）；缺失时显式失败。
- `BACKEND_PORT`、`FRONTEND_PORT` 未被占用；冲突时输出责任服务。
- 重复执行 `start` 会被拒绝，需先 `stop`。

## 运行时文件

- PID：`server/.runtime/<service>.pid`
- 日志：`server/logs/<service>.log`

完整行为契约见 [specs/001-fullstack-bootstrap/contracts/devctl-cli.md](../specs/001-fullstack-bootstrap/contracts/devctl-cli.md)，使用流程见 [quickstart.md](../specs/001-fullstack-bootstrap/quickstart.md)。
