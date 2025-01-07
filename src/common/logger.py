import logging
import sys

from common.constant import LOG_PATH


def setup_logging(
    server_name: str = "unknown",
    log_level: int = logging.INFO,
):
    log_path = LOG_PATH / f"{server_name}/worker.log"
    log_path.parent.exists() or log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(
        log_path,
        encoding="utf-8",
    )
    logging.basicConfig(
        format=f"[%(asctime)s] [%(levelname)s][{server_name}] [%(filename)s:%(lineno)s - %(funcName)s()] %(message)s",
        level=log_level,
        handlers=[
            logging.StreamHandler(sys.stdout),
            file_handler,
        ],
    )
