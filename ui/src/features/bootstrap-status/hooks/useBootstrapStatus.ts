import { useCallback, useEffect, useState } from "react";
import { DemoTaskStatus, HealthResponse, getDemoTaskStatus, getHealth, submitDemoTask } from "../api";

const POLL_INTERVAL_MS = 1000;
const POLL_TIMEOUT_MS = 15000;

interface TaskFlowState {
  status: DemoTaskStatus | null;
  error: string | null;
  running: boolean;
}

const idleTask: TaskFlowState = { status: null, error: null, running: false };

export function useBootstrapStatus() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [task, setTask] = useState<TaskFlowState>(idleTask);

  useEffect(() => {
    getHealth().then(setHealth).catch((error) => setHealthError(String(error)));
  }, []);

  const runDemoTask = useCallback(async (message: string) => {
    setTask({ status: null, error: null, running: true });
    try {
      const accepted = await submitDemoTask(message);
      const deadline = Date.now() + POLL_TIMEOUT_MS;
      let current: DemoTaskStatus = {
        task_id: accepted.task_id,
        state: accepted.state,
        result_message: null,
        error_message: null,
        started_at: null,
        finished_at: null,
      };
      while (current.state === "PENDING" || current.state === "STARTED") {
        if (Date.now() > deadline) {
          setTask({ status: current, error: "轮询超时", running: false });
          return;
        }
        await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
        current = await getDemoTaskStatus(accepted.task_id);
      }
      setTask({ status: current, error: null, running: false });
    } catch (error) {
      setTask({ status: null, error: String(error), running: false });
    }
  }, []);

  return { health, healthError, task, runDemoTask };
}
