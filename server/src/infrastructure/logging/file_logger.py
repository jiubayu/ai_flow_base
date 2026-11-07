from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

SECRET_PATTERN = re.compile(r"(?i)\b(token|secret|password|api_key)\b\s*=\s*\S+")


def redact(message: str) -> str:
    return SECRET_PATTERN.sub(lambda m: f"{m.group(1)}=[REDACTED]", message)


class FileLogger:
    """结构化文件日志写入器：每行带 UTC 时间戳与级别，敏感值脱敏。"""

    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, level: str, message: str) -> None:
        line = f"{datetime.now(timezone.utc).isoformat()} [{level}] {redact(message)}"
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
