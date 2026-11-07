class TaskNotFoundError(Exception):
    def __init__(self, task_id: str) -> None:
        super().__init__(f"任务不存在：{task_id}")
        self.task_id = task_id
