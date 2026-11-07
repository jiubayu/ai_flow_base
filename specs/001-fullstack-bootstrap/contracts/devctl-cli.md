# Devctl CLI Contract

## 命令入口

```bash
./scripts/devctl.sh <subcommand>
```

## 支持的子命令

### `start`

- 作用：依次启动 `backend`、`celery`、`frontend`
- 成功条件：
  - `backend` 与 `frontend` 通过健康探针
  - `celery` 进程保持存活
  - 输出日志目录；失败时输出责任服务的日志路径
  - 输出最小联通验证入口提示
- 失败条件：
  - 任一必填配置缺失
  - 端口冲突
  - 服务进程退出或健康探针失败
  - 任一服务失败后，脚本必须清理本次已启动的其他服务

### `stop`

- 作用：停止由 `devctl` 启动的全部服务
- 成功条件：
  - 已记录的 PID 全部被清理
  - 再次查询状态时不再显示为 `running`
- 失败条件：
  - PID 文件存在但进程已失效时，必须显式提示并执行清理

### `status`

- 作用：查询 `backend`、`celery`、`frontend` 当前状态
- 输出字段：
  - `service`
  - `state`
  - `pid`
  - `log_path`
  - `message`
- 状态枚举：
  - `running`
  - `stopped`
  - `failed`

## 输出约束

- 成功与失败都必须有明确结论，不允许静默结束
- 错误输出必须指出责任服务与建议查看的日志文件
- 所有输出使用面向开发者的中文文案
- `status` 在存在失效 PID 时必须输出已清理提示或失败状态，不得静默忽略
