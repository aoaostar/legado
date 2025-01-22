import logging
import os
import pickle

from common.constant import TEMP_SOURCES_PATH
from utils import hash_utils


class FileStateService:
    state_file = TEMP_SOURCES_PATH / "file_state.pkl"

    async def restore(self):
        if not self.state_file.exists():
            return
        store = pickle.loads(self.state_file.read_bytes())
        restore_files = []
        for p, _, filenames in TEMP_SOURCES_PATH.walk():
            for filename in filenames:
                file_path = p / filename
                k = hash_utils.file_sha1(file_path)
                if k not in store:
                    continue

                os.utime(file_path, (store[k], store[k]))
                restore_files.append(file_path)
        logging.info(
            f"文件状态已从[{self.state_file}]恢复, 恢复文件数: {len(restore_files)}"
        )

    async def save(self):
        store = {}
        for p, _, filenames in TEMP_SOURCES_PATH.walk():
            for filename in filenames:
                file_path = p / filename
                k = hash_utils.file_sha1(file_path)
                v = file_path.stat().st_mtime
                store[k] = v
        self.state_file.write_bytes(pickle.dumps(store))
        logging.info(f"文件状态已保存到[{self.state_file}]")
