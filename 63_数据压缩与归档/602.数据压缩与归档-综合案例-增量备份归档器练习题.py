# ===== 第602课：数据压缩与归档-综合案例-增量备份归档器 =====
# 知识点：
#   - 增量备份：只对「新增 + 内容变化」的文件打包，靠内容哈希判断变化
#   - 快照 manifest：记录 相对路径 -> sha256，作为下一轮的比较基准
#   - 删除检测：上一轮有、这一轮没有的条目即为删除
#   - 每轮归档自带 manifest.json，说明本轮变更，便于审计与回放
#   - 综合用到 hashlib / json / zipfile / pathlib / tempfile
# 依赖：无（标准库）
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path


def digest(path: Path) -> str:
    """分块计算 sha256，避免大文件一次性读入内存。"""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def snapshot(src: Path) -> dict:
    """生成 {相对路径: 内容哈希} 快照。"""
    return {
        str(p.relative_to(src)): digest(p)
        for p in sorted(src.rglob("*"))
        if p.is_file()
    }


def incremental_backup(src: Path, work: Path, state_file: Path):
    """对比快照，把变更文件打进新的 zip，并更新状态文件。"""
    current = snapshot(src)
    previous = json.loads(state_file.read_text("utf-8")) if state_file.exists() else {}
    changed = [name for name, h in current.items() if previous.get(name) != h]
    deleted = [name for name in previous if name not in current]

    work.mkdir(parents=True, exist_ok=True)
    index = len(list(work.glob("backup_*.zip"))) + 1
    archive = work / f"backup_{index:03d}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for name in changed:
            z.write(src / name, name)
        z.writestr("manifest.json", json.dumps(
            {"changed": changed, "deleted": deleted, "total": len(current)},
            ensure_ascii=False, indent=2,
        ))
    state_file.write_text(json.dumps(current, ensure_ascii=False, indent=2), "utf-8")
    return archive, changed, deleted


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    src = root / "docs"
    src.mkdir()
    (src / "a.txt").write_text("版本 1", "utf-8")
    (src / "sub").mkdir()
    (src / "sub" / "b.txt").write_text("数据 B", "utf-8")
    state = root / "state.json"
    work = root / "backups"

    for round_no in (1, 2, 3):
        if round_no == 2:
            (src / "a.txt").write_text("版本 2（已修改）", "utf-8")
            (src / "c.txt").write_text("新增文件", "utf-8")
        if round_no == 3:
            (src / "sub" / "b.txt").unlink()
        archive, changed, deleted = incremental_backup(src, work, state)
        print(f"== 第 {round_no} 轮 ==")
        print(f"  归档：{archive.name}（{archive.stat().st_size} 字节）")
        print(f"  变更/新增：{changed}")
        print(f"  删除：{deleted}")

    print("\n== 归档清单 ==")
    for p in sorted(work.glob("*.zip")):
        with zipfile.ZipFile(p) as z:
            manifest = json.loads(z.read("manifest.json"))
            print(f"  {p.name}: {z.namelist()}")
            print(f"    manifest: changed={len(manifest['changed'])} deleted={len(manifest['deleted'])} total={manifest['total']}")

    print("\n== 最终状态 ==")
    print("  ", json.loads(state.read_text("utf-8")))

# ===== 练习题 =====
# 1. 增加「只备份最近 7 天修改过的文件」的时间过滤条件。
# 2. 实现 restore(archive, dest)，按 manifest 把某轮归档还原到目录。
# 3. 给备份文件加上时间戳命名，并保留最近 N 份、删除更早的归档。
# 4. 思考：用内容哈希而不是修改时间判断变化，各有什么优缺点？
