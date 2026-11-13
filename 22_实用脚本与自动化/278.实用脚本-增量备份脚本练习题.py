# ===== 第278课：实用脚本-增量备份脚本 =====
# 知识点：
#   - 备份 = 复制 + 清单 + 校验；哈希判断“文件变没变”（第265课）
#   - 增量备份：只复制哈希有变化的文件，其余跳过
#   - 清单存 JSON：路径 → sha256（复习第232课）

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

SRC = Path("backup_src")
BACKUP = Path("backup_out")

# 准备源文件
SRC.mkdir(exist_ok=True)
(SRC / "report.txt").write_text("v1 内容", encoding="utf-8")
(SRC / "data.csv").write_text("a,b\n1,2", encoding="utf-8")


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def backup(src: Path, backup_dir: Path):
    backup_dir.mkdir(exist_ok=True)
    manifest_path = backup_dir / "manifest.json"
    old = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.exists()
        else {}
    )
    new = {}
    copied = []
    for f in src.rglob("*"):
        if f.is_file():
            rel = str(f.relative_to(src))
            digest = file_sha256(f)
            new[rel] = digest
            if old.get(rel) != digest:          # 哈希变化（或新文件）才复制
                target = backup_dir / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, target)          # copy2 连同修改时间一起复制
                copied.append(rel)
    manifest_path.write_text(
        json.dumps(
            {"时间": datetime.now().isoformat(timespec="seconds"), "files": new},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    return copied


print("第 1 次备份，复制：", backup(SRC, BACKUP))
print("第 2 次备份（无变化），复制：", backup(SRC, BACKUP))

(SRC / "report.txt").write_text("v2 新内容", encoding="utf-8")
print("第 3 次备份（改 1 个文件），复制：", backup(SRC, BACKUP))

shutil.rmtree(SRC)
shutil.rmtree(BACKUP)

# ===== 练习题 =====
# 1. 给 backup 增加“删除检测”：源里被删的文件，从清单标出。
# 2. 把复制改成“打包成 zip”（结合第277课），一次压缩替代散文件。
# 3. 思考：为什么用哈希对比而不是 mtime？（提示：mtime 变了内容不一定变）
