import { httpJson } from "../../shared/lib/http";

export interface HealthResponse {
  status: string;
  service: string;
  timestamp: string;
  debug?: boolean;
}

export type TaskState = "PENDING" | "STARTED" | "SUCCESS" | "FAILURE";

export interface DemoTaskAccepted {
  task_id: string;
  state: TaskState;
  message: string;
}

export interface DemoTaskStatus {
  task_id: string;
  state: TaskState;
  result_message: string | null;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
}

export function getHealth(): Promise<HealthResponse> {
  return httpJson<HealthResponse>("/api/health");
}

export function submitDemoTask(message: string): Promise<DemoTaskAccepted> {
  return httpJson<DemoTaskAccepted>("/api/dev/tasks/demo", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export function getDemoTaskStatus(taskId: string): Promise<DemoTaskStatus> {
  return httpJson<DemoTaskStatus>(`/api/dev/tasks/${taskId}`);
}
