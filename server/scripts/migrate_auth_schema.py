#!/usr/bin/env python3
"""认证与工作空间 SQLite schema 幂等迁移入口。

用法：cd server && uv run python scripts/migrate_auth_schema.py
失败时停止执行并保留原数据库文件；不自动删除已有表。
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
from src.infrastructure.persistence.auth_migrations import run_migrations, verify_migration


def main() -> int:
    config = load_config()
    logger = configure_logging(FileLogger(config.log_dir / "backend.log"), "backend", config.debug)
    logger.info(f"认证迁移开始：{config.celery_result_db_path}")

    try:
        created = run_migrations(config.celery_result_db_path, logger)
    except Exception as exc:
        logger.error(f"认证迁移失败：{exc}；原数据库文件保持不变")
        print(f"迁移失败：{exc}", file=sys.stderr)
        return 1

    missing = verify_migration(config.celery_result_db_path)
    if missing:
        logger.error(f"认证迁移验证失败：缺失 {missing}")
        print(f"迁移验证失败：缺失 {missing}", file=sys.stderr)
        return 1

    try:
        ws_created = workspace_migrations.run_migrations(config.celery_result_db_path, logger)
        engine = create_engine(f"sqlite:///{config.celery_result_db_path}", future=True)
        bad_counts = {k: v for k, v in workspace_migrations.run_validation_queries(engine).items() if v}
    except Exception as exc:
        logger.error(f"工作空间迁移失败：{exc}；原数据库文件保持不变")
        print(f"工作空间迁移失败：{exc}", file=sys.stderr)
        return 1

    ws_missing = workspace_migrations.verify_migration(config.celery_result_db_path)
    if ws_missing:
        logger.error(f"工作空间迁移验证失败：缺失 {ws_missing}")
        print(f"工作空间迁移验证失败：缺失 {ws_missing}", file=sys.stderr)
        return 1
    if bad_counts:
        logger.error(f"工作空间数据验证失败：{bad_counts}")
        print(f"工作空间数据验证失败：{bad_counts}", file=sys.stderr)
        return 1

    print(f"迁移完成：{config.celery_result_db_path}")
    print(f"本次新建表：{created or '无（全部已存在）'}")
    print("验证通过：5 张认证表、唯一索引与关键列均存在")
    print(f"工作空间本次新建表：{ws_created or '无（全部已存在）'}")
    print("工作空间验证通过：4 张表、username 列、ux_memberships_active 索引与验证 SQL 计数全为 0")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ConfigError as exc:
        print(f"配置错误：{exc}", file=sys.stderr)
        raise SystemExit(1)
