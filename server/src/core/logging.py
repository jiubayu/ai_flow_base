from __future__ import annotations

import logging
from typing import Protocol


class LogSink(Protocol):
    def write(self, level: str, message: str) -> None: ...


class SinkHandler(logging.Handler):
    def __init__(self, sink: LogSink) -> None:
        super().__init__()
        self.sink = sink

    def emit(self, record: logging.LogRecord) -> None:
        self.sink.write(record.levelname, record.getMessage())


def configure_logging(sink: LogSink, service: str, debug: bool = False) -> logging.Logger:
    logger = logging.getLogger(f"bootstrap.{service}")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.handlers.clear()
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(f"[%(levelname)s] [{service}] %(message)s"))
    logger.addHandler(console)
    logger.addHandler(SinkHandler(sink))
    return logger
