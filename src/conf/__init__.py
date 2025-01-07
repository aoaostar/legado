import os
from pathlib import Path
from typing import TypeVar

import yaml
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def load_yml_config(filename: os.PathLike | str) -> dict | list:
    filename = Path(filename)

    if not filename.exists():
        raise FileNotFoundError(f"配置文件 '{filename}' 不存在")

    read_text = filename.read_text(encoding="utf-8")
    return yaml.safe_load(read_text)
