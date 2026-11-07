#!/usr/bin/env python3
"""工作空间与应用 SQLite schema 幂等迁移入口（005）。

用法：cd server && uv run python scripts/migrate_workspace_schema.py
创建 workspaces / workspace_memberships / user_workspace_preferences /
workspace_audit_events / workspace_applications 表及唯一约束；重复执行安全。
失败时停止执行并保留原数据库文件；不自动删除已有表。
回滚方式：删除本次新建的表，或恢复迁移前的数据库备份。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine

from src.core.config import ConfigError, load_config
from src.core.logging import configure_logging
from src.infrastructure.logging.file_logger import FileLogger
from src.infrastructure.persistence import workspace_migrations
from src.infrastructure.persistence.auth_migrations import run_migrations as run_auth_migrations


def main() -> int:
    config = load_config()
    logger = configure_logging(FileLogger(config.log_dir / "backend.log"), "backend", config.debug)
    db_path = config.celery_result_db_path
    logger.info(f"工作空间迁移开始：{db_path}")

    try:
        # 认证表是工作空间外键回填的前提；auth 迁移本身幂等。
        run_auth_migrations(db_path, logger)
        created = workspace_migrations.run_migrations(db_path, logger)
        engine = create_engine(f"sqlite:///{db_path}", future=True)
        bad_counts = {k: v for k, v in workspace_migrations.run_validation_queries(engine).items() if v}
    except Exception as exc:
        logger.error(f"工作空间迁移失败：{exc}；原数据库文件保持不变")
        print(f"迁移失败：{exc}", file=sys.stderr)
        return 1

    missing = workspace_migrations.verify_migration(db_path)
    if missing:
        logger.error(f"工作空间迁移验证失败：缺失 {missing}")
        print(f"迁移验证失败：缺失 {missing}", file=sys.stderr)
        return 1
    if bad_counts:
        logger.error(f"工作空间数据验证失败：{bad_counts}")
        print(f"工作空间数据验证失败：{bad_counts}", file=sys.stderr)
        return 1

    print(f"迁移完成：{db_path}")
    print(f"本次新建表：{created or '无（全部已存在）'}")
    print("验证通过：5 张工作空间表（含 workspace_applications）、唯一索引与验证 SQL 计数全部就绪")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ConfigError as exc:
        print(f"配置错误：{exc}", file=sys.stderr)
        raise SystemExit(1)
