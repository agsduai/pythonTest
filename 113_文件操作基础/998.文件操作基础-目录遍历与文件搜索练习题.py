# ===== 第998课：文件操作基础-目录遍历与文件搜索 =====
# 知识点：
#   - os.listdir() 列出目录下的所有文件和子目录
#   - os.mkdir() 创建目录
#   - glob.glob("*.txt") 按模式搜索文件
#   - os.remove() 删除文件
#   - 实际场景：批量处理文件、按类型筛选
# 依赖：无（标准库）
import os
import glob

# 案例一：创建目录和测试文件
os.makedirs("test_dir", exist_ok=True)
os.makedirs("test_dir/sub", exist_ok=True)
for name in ("notes.txt", "data.csv", "report.pdf", "photo.jpg"):
    path = os.path.join("test_dir", name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"内容: {name}")
print("== 创建了测试目录和文件 ==")

# 案例二：列出目录内容
print("\n== os.listdir 列出 test_dir ==")
entries = os.listdir("test_dir")
for entry in sorted(entries):
    full = os.path.join("test_dir", entry)
    file_type = "目录" if os.path.isdir(full) else "文件"
    size = os.path.getsize(full) if os.path.isfile(full) else 0
    print(f"  {entry:<16} [{file_type}] {size}B")

# 案例三：按类型筛选文件
print("\n== glob 按模式搜索 ==")
txt_files = glob.glob("test_dir/*.txt")
print(f"  *.txt 文件: {txt_files}")
csv_files = glob.glob("test_dir/*.csv")
print(f"  *.csv 文件: {csv_files}")
all_files = glob.glob("test_dir/*")
print(f"  所有文件: {all_files}")

# 案例四：只统计 .txt 文件的总大小
print("\n== 统计 .txt 文件总大小 ==")
total_size = 0
txt_count = 0
for txt in txt_files:
    total_size += os.path.getsize(txt)
    txt_count += 1
print(f"  {txt_count} 个 .txt 文件，总大小 {total_size} 字节")

# 案例五：批量重命名（加前缀）
print("\n== 批量重命名（加前缀）==")
for txt in txt_files:
    dirname = os.path.dirname(txt)
    filename = os.path.basename(txt)
    new_path = os.path.join(dirname, "backup_" + filename)
    if not os.path.exists(new_path):
        os.rename(txt, new_path)
        print(f"  {filename} -> backup_{filename}")
# 还原
for txt in glob.glob("test_dir/backup_*"):
    dirname = os.path.dirname(txt)
    filename = os.path.basename(txt)
    original = filename.replace("backup_", "")
    os.rename(txt, os.path.join(dirname, original))
print("  已还原文件名")

# 案例六：清理测试文件
os.remove("test_dir/notes.txt")
os.remove("test_dir/data.csv")
os.remove("test_dir/report.pdf")
os.remove("test_dir/photo.jpg")
os.rmdir("test_dir/sub")
os.rmdir("test_dir")
print(f"\n== 清理完成，test_dir 存在: {os.path.exists('test_dir')} ==")

# ===== 练习题 =====
# 1. 创建目录 my_files，在里面创建 3 个 .txt 文件，然后用 glob 找到它们。
# 2. 列出当前目录下所有 .py 文件的文件名和大小。
# 3. 统计某个目录中各种后缀文件的个数（.py/.txt/.csv）。
# 4. 思考：os.listdir() 和 glob.glob() 有什么区别？什么时候用哪个？
