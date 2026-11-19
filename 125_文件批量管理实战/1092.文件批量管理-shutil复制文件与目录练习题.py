# ===== 第1092课：文件批量管理-shutil复制文件与目录 =====
# 知识点：
#   - import shutil：shutil.copy 复制文件、copy2 连"修改时间"等元数据一起复制
#   - copytree(源目录, 目标目录)：整个目录树连子目录一起复制
#   - 目标目录必须不存在（copytree 直接建），存在会报 FileExistsError
#   - 本课全部在系统临时目录演练，结束自动清理，不碰你的真实文件

# 案例一：复制单个文件
import shutil
import os
import tempfile

work = tempfile.mkdtemp(prefix="py1092_")  # 建临时工作目录
src = os.path.join(work, "报告.txt")
with open(src, "w", encoding="utf-8") as f:
    f.write("季度报告内容")

dst = os.path.join(work, "备份_报告.txt")
shutil.copy(src, dst)
print(f"复制完成：{os.path.exists(dst)}，内容一致：{open(dst, encoding='utf-8').read() == '季度报告内容'}")

# 案例二：copy2 保留修改时间
import time

os.utime(src, (1000000000, 1000000000))  # 把修改时间设为固定值
shutil.copy(src, os.path.join(work, "copy1.txt"))
shutil.copy2(src, os.path.join(work, "copy2.txt"))
t1 = os.path.getmtime(os.path.join(work, "copy1.txt"))
t2 = os.path.getmtime(os.path.join(work, "copy2.txt"))
print(f"copy 后修改时间变了：{t1 != 1000000000}，copy2 保留原时间：{t2 == 1000000000}")

# 案例三：copytree 复制整个目录
# 场景：备份整个项目文件夹
proj = os.path.join(work, "我的项目")
os.makedirs(os.path.join(proj, "子目录"), exist_ok=True)
open(os.path.join(proj, "main.py"), "w").write("print('hi')")
open(os.path.join(proj, "子目录", "util.py"), "w").write("pass")

backup = os.path.join(work, "项目备份")  # 必须不存在
shutil.copytree(proj, backup)
copied = []
for root, dirs, files in os.walk(backup):
    for name in files:
        copied.append(os.path.relpath(os.path.join(root, name), backup))
print(f"备份内容：{sorted(copied)}")

# 案例四：dirs_exist_ok 覆盖式复制（Python 3.8+）
# 目标已存在时，加 dirs_exist_ok=True 可以合并复制
shutil.copytree(proj, backup, dirs_exist_ok=True)
print(f"二次备份成功（覆盖合并）：{os.path.exists(os.path.join(backup, 'main.py'))}")

# 收尾清理
shutil.rmtree(work)
print(f"临时目录已清理：{not os.path.exists(work)}")

# ===== 练习题 =====
# 1. 在临时目录创建 3 个 txt 文件，逐个 shutil.copy 复制为 "副本_xxx.txt"，打印复制后目录文件列表。
# 2. 写函数 backup_dir(src, dst)：用 copytree 备份目录，dst 已存在时自动加时间戳后缀再备份。
# 3. 验证 copy 与 copy2 的区别：改源文件修改时间后分别复制，打印两个副本的 getmtime 并解释差异。
