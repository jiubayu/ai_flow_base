from __future__ import annotations

from pathlib import Path

from kombu import Connection


def ensure_broker_dir(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def transport_options(directory: Path) -> dict:
    # 生产者写入 data_folder_in、消费者读取 data_folder_out；
    # 本地最小链路让两者指向同一目录，保证 API 与 worker 使用同一队列目录。
    path = str(directory)
    return {"data_folder_in": path, "data_folder_out": path, "store_processed": False}


def connect(url: str, directory: Path) -> Connection:
    ensure_broker_dir(directory)
    return Connection(url, transport="filesystem", transport_options=transport_options(directory))
