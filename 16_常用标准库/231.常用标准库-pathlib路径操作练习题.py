# ===== 第231课：常用标准库-pathlib路径操作 =====
# 知识点：
#   - pathlib.Path：面向对象的路径操作，比 os.path 更直观
#   - 拼路径用 / 运算符；name/stem/suffix/parent 拆路径
#   - mkdir(parents=True, exist_ok=True) 一行建多级目录
#   - glob / rglob：按模式查找文件（rglob 递归）
#   - read_text / write_text：小文件读写一步到位

import shutil
from pathlib import Path

# 路径的拼接与拆解
p = Path("demo_dir") / "sub" / "file.txt"
print(p)
print("文件名：", p.name, "| 主名：", p.stem, "| 后缀：", p.suffix)
print("上级目录：", p.parent)
print(p.with_suffix(".log"))      # 只改后缀

# 建目录 + 写文件（当前目录下演示，结束清理）
base = Path("pathlib_demo")
(base / "logs").mkdir(parents=True, exist_ok=True)
(base / "logs" / "a.txt").write_text("hello", encoding="utf-8")
(base / "b.txt").write_text("world", encoding="utf-8")

# 遍历与筛选
print("一级内容：", sorted(x.name for x in base.iterdir()))
print("递归找 txt：", sorted(str(f.relative_to(base)) for f in base.rglob("*.txt")))

for f in base.rglob("*.txt"):
    print(f.relative_to(base), f.stat().st_size, "字节")

# 判断与读取
f = base / "logs" / "a.txt"
print(f.exists(), f.is_file(), f.is_dir())
print(f.read_text(encoding="utf-8"))

# 绝对路径
print("绝对路径：", f.resolve())

shutil.rmtree(base)     # 清理演示目录

# ===== 练习题 =====
# 1. 创建“项目/docs/notes.md”多级结构，写入内容再读取打印。
# 2. 用 rglob 统计某个文件夹（如 11_装饰器与生成器）里 .py 文件的数量。
# 3. 编写函数 rename_suffix(dir, old, new)：把目录下所有 .txt 改成 .md（不真改，打印计划）。
# 4. 思考：pathlib.Path 和 os.path 函数能混用吗？
