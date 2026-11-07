# src：后端分层说明

```
src/
├── core/              # 配置加载与结构化日志引导（config.py, logging.py）
├── domain/            # 纯业务模型：实体、值对象、状态机，无外部依赖
│   └── bootstrap/     # DemoTask 状态机、ServiceDefinition、ServiceRuntimeStatus、TaskState/ServiceState
├── application/       # 用例编排：启动校验、任务提交/查询/处理、服务状态读模型
│   └── bootstrap/     # use_cases.py, services.py, errors.py
├── infrastructure/    # 外部依赖实现：Celery broker/tasks、SQLite result store、文件日志
│   ├── celery/
│   ├── persistence/
│   └── logging/
├── presentation/      # HTTP 层：路由与共享错误处理
│   └── api/           # health.py, dev_tasks.py
└── celery_app.py      # Celery 应用装配入口
```

## 边界规则

- `domain` 不 import 其他层；新增业务规则（状态迁移、校验）写在这里。
- `application` 编排用例，通过注入（如 `ResultStore`、`dispatch` 回调）使用 infrastructure 能力，便于测试替换。
- `infrastructure` 是具体实现（文件系统 broker、SQLite、文件日志）；替换真实 broker 只改这一层。
- `presentation` 只做 HTTP 出入参与错误映射，不承载业务规则。
- 新增 feature 时按同样结构建 `domain/<feature>/`、`application/<feature>/`、`presentation/api/<feature>.py`。
