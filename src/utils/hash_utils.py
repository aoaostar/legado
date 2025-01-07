import hashlib
from pathlib import Path


def sha1(str_content: str):
    s = hashlib.sha1()
    # noinspection PyTypeChecker
    s.update(str_content.encode("utf-8"))
    return s.hexdigest()


def short_hash_name(str_content: str, length: int = 8):
    return sha1(str_content)[:length]


def file_sha1(filepath: str | Path):
    s = hashlib.sha1()
    filepath = Path(filepath)
    with filepath.open("rb") as f:
        while True:
            b = f.read(2048)
            if not b:
                break
            # noinspection PyTypeChecker
            s.update(b)
    return s.hexdigest()
