#!/usr/bin/env python3
"""PostgreSQL（pgvector）schema 幂等迁移入口。

用法：cd server && uv run python scripts/migrate_postgres_schema.py
验证失败时退出码为 1；不读取、不导入、不删除旧 SQLite 文件。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
SERVER_DIR = CURRENT_DIR.parent
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from src.core.config import ConfigError, load_config
from src.infrastructure.persistence.database import create_database_engine
from src.infrastructure.persistence.postgres_migrations import (
    initialize_postgres_schema,
    verify_postgres_schema,
)


def main() -> None:
    config = load_config()
    engine = create_database_engine(config)
    executed = initialize_postgres_schema(engine)
    verification = verify_postgres_schema(engine)
    ok = all(verification.values())
    print(
        json.dumps(
            {
                "database_url": config.database_url.rsplit("@", 1)[-1],
                "executed": executed,
                "verification": verification,
                "ok": ok,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except ConfigError as exc:
        print(f"配置错误：{exc}", file=sys.stderr)
        raise SystemExit(1)
