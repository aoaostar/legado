import shutil

from pathspec import PathSpec, patterns

from common.constant import ROOT_PATH

folder_path = ROOT_PATH

file_patterns = [
    ".git",
    ".github",
    "sources",
    "!runtime",
    "index.html",
    "README.md",
    "CNAME",
]

spec = PathSpec.from_lines(patterns.GitWildMatchPattern, file_patterns)

for item in folder_path.rglob("*"):
    if not item.is_file() and not item.is_dir():
        continue
    if not spec.match_file(item.relative_to(folder_path)):
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item, ignore_errors=True)
