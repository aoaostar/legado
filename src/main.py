import asyncio
import contextlib
import logging
import shutil

from common.constant import SOURCES_PATH
from common.logger import setup_logging
from services.file_state_service import FileStateService
from services.render_service import RenderService
from services.sync_service import SyncService


class Main:
    def __init__(self):
        setup_logging(self.__class__.__name__)

    async def execute(self):
        (
            ffs,
            sync_service,
            render_service,
        ) = (
            FileStateService(),
            SyncService(),
            RenderService(),
        )
        logging.info("开始恢复文件状态")
        await ffs.restore()
        logging.info("恢复文件状态完成")

        logging.info("开始同步数据")
        sync_result = await sync_service.execute()
        logging.info(f"同步数据完成")
        logging.info("开始渲染数据")
        await render_service.execute(sync_result)
        logging.info("渲染数据完成")

        logging.info("保存文件状态")
        await ffs.save()
        logging.info("保存文件状态完成")

        logging.info("同步数据到源目录")
        shutil.rmtree(SOURCES_PATH, ignore_errors=True)
        SOURCES_PATH.mkdir(parents=True, exist_ok=True)
        for result in sync_result:
            shutil.copy(
                result.output_path,
                SOURCES_PATH / result.output_path.name,
            )

        logging.info("同步数据到源目录完成")

    @classmethod
    def start(cls):
        with contextlib.suppress(KeyboardInterrupt):
            asyncio.run(cls().execute())


if __name__ == "__main__":
    Main.start()
