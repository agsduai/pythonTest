# ===== 第1095课：文件批量管理-大小统计与磁盘占用 =====
# 知识点：
#   - os.path.getsize(路径)：取文件大小（字节）；目录没有直接 getsize，要遍历累加
#   - 单位换算：1024 字节 = 1KB，1024KB = 1MB，写个 format_size 函数
#   - os.walk 遍历目录树统计总大小，找出"最占空间的文件"
#   - 实际场景：清理前看谁最占地方、统计文件夹总大小

# 案例一：单个文件大小
import os
import shutil
import tempfile

work = tempfile.mkdtemp(prefix="py1095_")
f = os.path.join(work, "数据.txt")
content = "A" * 2048  # 写 2048 个字符
with open(f, "w", encoding="utf-8") as fp:
    fp.write(content)
size = os.path.getsize(f)
print(f"文件大小：{size} 字节（{size / 1024:.1f} KB）")

# 案例二：单位换算函数
def format_size(num_bytes):
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"

for s in [512, 2048, 5 * 1024 * 1024, 2 * 1024 * 1024 * 1024]:
    print(f"{s} 字节 = {format_size(s)}")

# 案例三：目录总大小 —— os.walk 累加
# 场景：统计"下载"文件夹一共占了多少空间
downloads = os.path.join(work, "下载")
os.makedirs(downloads)
files = {"电影.mp4": 1024 * 1024 * 3, "音乐.mp3": 1024 * 500, "文档.pdf": 2048}
for name, fake_size in files.items():
    path = os.path.join(downloads, name)
    with open(path, "wb") as fp:
        fp.write(b"\0" * fake_size)  # 写入指定大小的空内容

total = 0
for root, dirs, names in os.walk(downloads):
    for name in names:
        total += os.path.getsize(os.path.join(root, name))
print(f"下载文件夹总大小：{format_size(total)}")

# 案例四：找出最大的文件 TopN
# 场景：磁盘空间不足，找最占空间的文件
entries = []
for root, dirs, names in os.walk(downloads):
    for name in names:
        path = os.path.join(root, name)
        entries.append((os.path.getsize(path), name))
entries.sort(reverse=True)
for size, name in entries:
    print(f"{format_size(size):>12}  {name}")

# 收尾清理
shutil.rmtree(work)
print(f"临时目录已清理：{not os.path.exists(work)}")

# ===== 练习题 =====
# 1. 写函数 dir_size(path)：用 os.walk 返回目录总字节数，空目录应返回 0。
# 2. 修改 format_size：小于 1MB 显示 KB 保留 1 位小数，加上"共 X.X MB（Y 字节）"的双单位输出。
# 3. 综合题：统计临时目录里每个"子目录"各占多少字节，按从大到小打印（提示：对每个子目录分别 dir_size）。
