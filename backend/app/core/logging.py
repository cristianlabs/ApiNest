import sys

from loguru import logger

logger.remove()
logger.configure(extra={"request_id": "-"})
logger.add(
    sys.stdout,
    level="INFO",
    enqueue=True,
    backtrace=False,
    diagnose=False,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
        "req_id={extra[request_id]} | {message}"
    ),
)

__all__ = ["logger"]
