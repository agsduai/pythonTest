# ===== 第237课：常用标准库-综合案例-文件整理器 =====
# 知识点：
#   - 综合运用：pathlib 遍历 + shutil 移动 + json 报告 + datetime 时间戳
#   - 场景：把“下载目录”里的散落文件按扩展名自动归类
#   - 未知类型放 others，全程生成 JSON 整理报告

import json
import shutil
from datetime import datetime
from pathlib import Path

WORK = Path("organize_demo")

# 准备一堆“乱七八糟”的演示文件
(WORK / "photos").mkdir(parents=True, exist_ok=True)
for name in ("a.jpg", "b.png", "notes.txt", "report.pdf", "song.mp3", "未知.abc"):
    (WORK / name).write_text("demo", encoding="utf-8")

# 归类规则：扩展名 → 目标目录
RULES = {
    ".jpg": "photos",
    ".png": "photos",
    ".txt": "docs",
    ".pdf": "docs",
    ".mp3": "music",
}

report = {"整理时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "移动记录": []}

# 遍历 + 移动
for f in WORK.iterdir():
    if f.is_file():
        target_name = RULES.get(f.suffix.lower(), "others")   # 未知类型进 others
        dest = WORK / target_name
        dest.mkdir(exist_ok=True)
        shutil.move(str(f), str(dest / f.name))
        report["移动记录"].append(f"{f.name} → {target_name}/")

# 生成 JSON 报告
report_path = WORK / "整理报告.json"
report_path.write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(report_path.read_text(encoding="utf-8"))

# 展示整理后的目录结构
for p in sorted(WORK.rglob("*")):
    tag = "目录" if p.is_dir() else "文件"
    print(f"[{tag}] {p.relative_to(WORK)}")

shutil.rmtree(WORK)     # 清理演示目录

# ===== 练习题 =====
# 1. 给整理器增加“按大小整理”：超过 1MB 的文件移入 big/ 目录。
# 2. 整理真实目录（如你的下载文件夹）前，先把 move 改成“只打印不移动”的演练模式。
# 3. 给报告增加“各目录文件数量统计”。
# 4. 思考：同名文件冲突怎么处理？（提示：重命名为 name(1).ext）
