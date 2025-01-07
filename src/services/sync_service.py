import asyncio
import contextlib
import json
import logging
from datetime import datetime

import settings
from common.constant import STORAGE_PATH, TEMP_SOURCES_PATH
from conf import sources
from conf.models.BaseSouce import BaseSource
from conf.models.Souces import BookSource
from models.sync import SyncResult, SyncStatus
from utils import hash_utils
from utils.http_request import http_request


class SyncService:
    def __init__(self):
        self.__queue = asyncio.Queue(maxsize=settings.max_concurrent)
        self.__stop_token = asyncio.Event()

        self.sources = [
            *sources.book_sources,
            *sources.http_ttss,
            *sources.read_configs,
            *sources.replace_rules,
            *sources.subscribes,
            *sources.themes,
        ]
        self.__results: dict[int, SyncResult] = {}

    async def execute(self):
        ts = []
        for _ in range(max(1, self.__queue.maxsize)):
            ts.append(asyncio.create_task(self.worker()))

        for index, s in enumerate(self.sources):
            await self.__queue.put((index, s))

        await self.__queue.join()
        self.__stop_token.set()
        for t in ts:
            t.cancel()

        sorted_result: list[SyncResult] = [
            value for key, value in sorted(self.__results.items())
        ]

        merge_book_result = await self.__merge_book_sources(sorted_result)

        return [
            *merge_book_result,
            *sorted_result,
        ]

    async def __merge_book_sources(self, from_result: list[SyncResult]):
        # save all book sources to a single file

        all_book_source_path = TEMP_SOURCES_PATH / "all.temp"
        book_source_result_collection = []
        for r in from_result:
            if r.status == SyncStatus.Success and isinstance(r.source, BookSource):
                arr = json.loads(r.output_path.read_text(encoding="utf-8"))
                if not isinstance(arr, list):
                    continue
                for item in arr:
                    book_source_result_collection.append(item)

        all_book_source_path.write_text(
            json.dumps(
                book_source_result_collection,
                ensure_ascii=True,
            ),
            encoding="utf-8",
        )

        result = await self.sync(
            BookSource(
                title="全量书源",
                url=str(all_book_source_path),
            )
        )
        all_book_source_path.unlink(missing_ok=True)
        return [result]

    async def worker(self):
        while not self.__stop_token.is_set():
            try:
                index, source = await self.__queue.get()
                self.__results[index] = await self.sync(source)
            except asyncio.CancelledError:
                break
            except BaseException:
                logging.exception("worker error")
            finally:
                with contextlib.suppress(ValueError):
                    self.__queue.task_done()

    # noinspection PyMethodMayBeStatic
    async def __filter(self, source: BaseSource, origin_data: dict):
        match source:
            case BookSource():
                if not isinstance(origin_data, list):
                    raise ValueError("书源数据格式错误")
                return origin_data
            case _:
                return origin_data

    async def sync(self, source: BaseSource) -> SyncResult:
        logging.info(f"[{source.title}] 开始同步 {source.url}")

        hash_name = hash_utils.sha1(source.url)[:8]
        file_path = TEMP_SOURCES_PATH / f"{hash_name}.json"

        result = SyncResult(
            source=source,
            status=SyncStatus.Pending,
            message="同步成功",
            output_path=file_path,
            update_time=datetime.now(),
            sync_time=datetime.now(),
            count=0,
        )

        try:
            if source.url.startswith(("http://", "https://")):
                r = await http_request.get(source.url)
                r.raise_for_status()
                origin_data = r.json()
                serialized_data = json.dumps(origin_data)
            else:
                serialized_data = (STORAGE_PATH / source.url).read_text(
                    encoding="utf-8"
                )
                origin_data = json.loads(serialized_data)

            origin_data = await self.__filter(source, origin_data)
            changed = True

            if file_path.exists():
                hash_str = hash_utils.sha1(serialized_data)
                old_hash_str = hash_utils.file_sha1(file_path)
                if hash_str == old_hash_str:
                    changed = False

            if changed:
                file_path.write_text(
                    serialized_data,
                    encoding="utf-8",
                )
                result.update_time = datetime.now()
            else:
                logging.info(f"[{source.title}]数据未发生变化")
                result.update_time = datetime.fromtimestamp(file_path.stat().st_ctime)

            result.output_path = file_path
            result.status = SyncStatus.Success
            result.count = len(origin_data)

            logging.info(f"[{source.title}]同步完成: 共计 {result.count} 条")
        except Exception as e:
            logging.error(f"[{source.title}]同步失败")
            result.status = SyncStatus.Failed
            result.message = str(e)

            if file_path.exists():
                result.count = len(json.loads(file_path.read_text(encoding="utf-8")))

        return result
