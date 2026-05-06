import json
import logging
from datetime import datetime
from pathlib import Path


def setup_logger(name: str) -> logging.Logger:
    """ساخت لاگر با فرمت یکسان برای همه ماژول‌ها."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            fmt="[%(asctime)s] %(levelname)-8s %(name)s » %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    logger.addHandler(handler)
    return logger


def timestamp() -> str:
    """برگرداندن timestamp فعلی برای نام‌گذاری فایل‌ها."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_text(path: Path, content: str) -> None:
    """ذخیره رشته متنی در فایل."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def save_json(path: Path, data: dict) -> None:
    """ذخیره دیکشنری به فرمت JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_text(path: Path) -> str:
    """بارگذاری محتوای فایل متنی."""
    return path.read_text(encoding="utf-8")