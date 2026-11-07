# features/bootstrap-status

展示后端健康状态并驱动示例任务闭环（提交 → 轮询 → SUCCESS/FAILURE/超时）。

```
bootstrap-status/
├── api.ts                          # 后端 API 适配：/api/health、POST /api/dev/tasks/demo、GET /api/dev/tasks/<id>
├── hooks/useBootstrapStatus.ts     # 状态 hook：健康检查 + 任务轮询（1s 间隔、15s 超时）
└── components/BootstrapStatusPanel.tsx  # 展示层，使用 shared/StatusCard
```

约定：feature 内部只通过 `shared/lib/http.ts` 发请求（base URL 来自 `VITE_API_BASE_URL`）；展示组件复用 `shared/components/StatusCard`。feature 之间不互相 import。
