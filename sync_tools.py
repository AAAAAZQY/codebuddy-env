from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent

SRC_TOOLBOX = Path(r"D:\Codebuddy\toolbox")
SRC_EXT_SRC = Path(r"D:\Codebuddy\ext-src")
SRC_LEGACY_TOOLS = Path(r"D:\Codebuddy\tools")

DST_TOOLBOX = ROOT / "tools" / "toolbox"
DST_EXT_SRC = ROOT / "extensions"
DST_LEGACY_TOOLS = ROOT / "archive" / "legacy-tools"

IGNORE = shutil.ignore_patterns(
    "__pycache__",
    "*.pyc",
    "*.log",
    "*.tmp",
    "*.vsix",
    "node_modules",
    "out",
    "dist",
    ".DS_Store",
)


def sync_dir(src, dst):
    if not src.is_dir():
        print("SKIP missing:", src)
        return
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst, ignore=IGNORE)
    print("SYNC", src, "->", dst)


sync_dir(SRC_TOOLBOX, DST_TOOLBOX)
sync_dir(SRC_EXT_SRC, DST_EXT_SRC)
sync_dir(SRC_LEGACY_TOOLS, DST_LEGACY_TOOLS)
print("DONE")
