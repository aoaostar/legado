from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel

from conf.models.BaseSouce import BaseSource


class SyncStatus(Enum):
    Pending = "同步中"
    Success = "同步成功"
    Failed = "同步失败"


class SyncResult(BaseModel):
    source: BaseSource
    status: SyncStatus
    message: str
    output_path: Path
    count: int
    update_time: datetime
    sync_time: datetime
