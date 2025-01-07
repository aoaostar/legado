import asyncio
import contextlib
import logging
import shutil

from common.constant import SOURCES_PATH, TEMP_SOURCES_PATH
from common.logger import setup_logging
from services.render_service import RenderService
from services.sync_service import SyncService


class Main:
    def __init__(self):
        setup_logging(self.__class__.__name__)

    async def execute(self):
        sync_service = SyncService()
        render_service = RenderService()

        logging.info("开始同步数据")
        sync_result = await sync_service.execute()
        logging.info(f"同步数据完成")
        logging.info("开始渲染数据")
        await render_service.execute(sync_result)
        logging.info("渲染数据完成")
        shutil.copytree(
            TEMP_SOURCES_PATH,
            SOURCES_PATH,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(
                "*.temp",
            ),
        )
        logging.info("同步数据到源目录完成")

    @classmethod
    def start(cls):
        with contextlib.suppress(KeyboardInterrupt):
            asyncio.run(cls().execute())


if __name__ == "__main__":
    Main.start()
