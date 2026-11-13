# ===== 第279课：实用脚本-文件监控 =====
# 知识点：
#   - 监控思路：周期快照（路径→mtime）对比上一次 → 发现新增/修改/删除
#   - 集合运算：keys 差集与交集让三类事件一目了然
#   - 轮询是最朴素的方案；生产可换 watchdog 库（事件驱动，扩展阅读）

import shutil
import time
from pathlib import Path

WATCH = Path("watch_demo")
WATCH.mkdir(exist_ok=True)
target = WATCH / "log.txt"
target.write_text("v1", encoding="utf-8")


def snapshot(root: Path):
    """当前状态：相对路径 -> 修改时间。"""
    return {
        str(p.relative_to(root)): p.stat().st_mtime
        for p in root.rglob("*")
        if p.is_file()
    }


prev = snapshot(WATCH)
print("开始监控（3 轮，每轮 0.5 秒）...")

for round_no in range(1, 4):
    time.sleep(0.5)
    # 按轮次模拟文件变动
    if round_no == 1:
        (WATCH / "new.txt").write_text("新增文件", encoding="utf-8")
    elif round_no == 2:
        target.write_text("v2 修改内容", encoding="utf-8")
    elif round_no == 3:
        (WATCH / "new.txt").unlink()

    cur = snapshot(WATCH)
    for name in cur.keys() - prev.keys():
        print(f"  [新增] {name}")
    for name in prev.keys() - cur.keys():
        print(f"  [删除] {name}")
    for name in cur.keys() & prev.keys():
        if cur[name] != prev[name]:
            print(f"  [修改] {name}")
    prev = cur

shutil.rmtree(WATCH)

# ===== 练习题 =====
# 1. 把“3 轮演示”改成 while True 死循环，用 Ctrl+C 退出（KeyboardInterrupt）。
# 2. 监控到变化时写一条日志到 watch.log（结合第216课 logging）。
# 3. 思考：监控 10 万个文件的目录，这份快照代码有什么问题？如何只扫一层？
