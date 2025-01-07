from pathlib import Path

EXECUTE_PATH = Path.cwd()
ROOT_PATH = EXECUTE_PATH

SOURCE_PATH = ROOT_PATH / "src"
CONF_PATH = ROOT_PATH / "conf"
RUNTIME_PATH = ROOT_PATH / "runtime"
LOG_PATH = RUNTIME_PATH / "logs"

STORAGE_PATH = CONF_PATH / "storage"
TEMP_SOURCES_PATH = RUNTIME_PATH / "sources"
SOURCES_PATH = ROOT_PATH / "sources"


for p in [
    RUNTIME_PATH,
    LOG_PATH,
    STORAGE_PATH,
    TEMP_SOURCES_PATH,
    SOURCES_PATH,
]:
    p.exists() or p.mkdir(parents=True, exist_ok=True)
