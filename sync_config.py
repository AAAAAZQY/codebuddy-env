from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent

SRC_RULES = Path(r"C:\Users\myages2026\.codebuddy\rules")
SRC_MEMORIES = Path(r"D:\Codebuddy\memories")
SRC_PROJECTS = Path(r"C:\Users\myages2026\.codebuddy\projects")

DST_RULES = ROOT / "rules"
DST_MEMORY = ROOT / "memory"
DST_PROJECT_MEMORY = ROOT / "codebuddy-project-memory"

IGNORE = shutil.ignore_patterns(
    "__pycache__",
    "*.pyc",
    "*.tmp",
    "*.log",
    "*.bak",
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


def sync_project_memory():
    if DST_PROJECT_MEMORY.exists():
        shutil.rmtree(DST_PROJECT_MEMORY)
    DST_PROJECT_MEMORY.mkdir(parents=True, exist_ok=True)

    if not SRC_PROJECTS.is_dir():
        print("SKIP missing:", SRC_PROJECTS)
        return

    count = 0
    for src in SRC_PROJECTS.glob("*/*/memory/MEMORY.md"):
        rel = src.relative_to(SRC_PROJECTS).parent.parent
        dst_dir = DST_PROJECT_MEMORY / rel
        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst_dir / "MEMORY.md")
        count += 1

    print("SYNC project memory files:", count)


sync_dir(SRC_RULES, DST_RULES)
sync_dir(SRC_MEMORIES, DST_MEMORY)
sync_project_memory()
print("DONE")
