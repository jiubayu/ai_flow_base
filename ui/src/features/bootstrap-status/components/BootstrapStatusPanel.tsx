import { useState } from "react";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { StatusCard } from "@/shared/components/StatusCard";
import { useBootstrapStatus } from "../hooks/useBootstrapStatus";

export function BootstrapStatusPanel() {
  const { health, healthError, task, runDemoTask } = useBootstrapStatus();
  const [message, setMessage] = useState("bootstrap smoke");

  const healthState = healthError ? "error" : health ? health.status : "unknown";
  const healthMessage =
    healthError ?? (health ? `service=${health.service} @ ${health.timestamp}` : "等待健康响应");

  const taskState = task.error ? "error" : task.status?.state ?? "idle";
  const taskMessage =
    task.error ?? task.status?.result_message ?? task.status?.error_message ?? "尚未提交";

  return (
    <div className="mx-auto max-w-xl space-y-t-4 p-t-6">
      <h1 className="text-level-1">Bootstrap Status</h1>
      <StatusCard title="后端健康" state={healthState} message={healthMessage} />
      <div className="space-y-t-2">
        <Input value={message} onChange={(event) => setMessage(event.target.value)} placeholder="示例任务消息" />
        <Button onClick={() => runDemoTask(message)} disabled={task.running}>
          {task.running ? "处理中…" : "提交示例任务"}
        </Button>
      </div>
      <StatusCard title="示例任务" state={taskState} message={taskMessage} />
    </div>
  );
}
