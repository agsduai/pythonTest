# ===== 第1099课：文件批量管理-综合案例-照片整理器 =====
# 知识点：
#   - 综合运用：遍历 + 扩展名分类 + 批量重命名 + 大小统计 + 冲突处理
#   - 整理器套路：扫描 -> 规则分类 -> 归档移动 -> 输出报告
#   - 移动前统计、移动后核对，保证"一张不丢"
#   - 全程在临时目录演练，结束自动清理

# 案例一：造一个"乱七八糟"的相册目录
import os
import shutil
import tempfile

work = tempfile.mkdtemp(prefix="py1099_")
messy = os.path.join(work, "待整理")
os.makedirs(messy)
seeds = [
    ("IMG_001.jpg", 300), ("IMG_002.jpg", 1500), ("截图.png", 200),
    ("视频A.mp4", 8000), ("视频B.mov", 9000), ("IMG_003.jpg", 400),
    ("说明.txt", 50), ("截图 (1).png", 250),
]
for name, size in seeds:
    with open(os.path.join(messy, name), "wb") as f:
        f.write(b"\0" * size)
before_count = len(os.listdir(messy))
print(f"待整理：{before_count} 个文件")

# 案例二：分类规则与执行
RULES = {
    ".jpg": "图片", ".jpeg": "图片", ".png": "图片", ".gif": "图片",
    ".mp4": "视频", ".mov": "视频", ".avi": "视频",
    ".txt": "文档",
}

def classify_folder(folder):
    moved = []
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        ext = os.path.splitext(name)[1].lower()
        sub = RULES.get(ext, "其他")
        target = os.path.join(folder, sub)
        os.makedirs(target, exist_ok=True)
        shutil.move(path, os.path.join(target, name))
        moved.append((name, sub))
    return moved

moved = classify_folder(messy)
for name, sub in moved:
    print(f"  {name} -> {sub}/")

# 案例三：图片重命名（按类别统一编号）
img_dir = os.path.join(messy, "图片")
for i, name in enumerate(sorted(os.listdir(img_dir)), start=1):
    ext = os.path.splitext(name)[1].lower()
    os.rename(os.path.join(img_dir, name), os.path.join(img_dir, f"照片_{i:03d}{ext}"))
print(f"图片重命名后：{sorted(os.listdir(img_dir))}")

# 案例四：整理报告 —— 各类数量与大小
def format_size(n):
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"

print("--- 整理报告 ---")
after_count = 0
for sub in sorted(os.listdir(messy)):
    sub_path = os.path.join(messy, sub)
    if not os.path.isdir(sub_path):
        continue
    files = os.listdir(sub_path)
    total = sum(os.path.getsize(os.path.join(sub_path, f)) for f in files)
    after_count += len(files)
    print(f"{sub}/：{len(files)} 个文件，共 {format_size(total)}")

# 案例五：完整性核对
print(f"整理前 {before_count} 个，整理后 {after_count} 个：{'一致，无丢失' if before_count == after_count else '有丢失！'}")

# 收尾清理
shutil.rmtree(work)
print(f"临时目录已清理：{not os.path.exists(work)}")

# ===== 练习题 =====
# 1. 给 classify_folder 增加"按月份分二级目录"（文件名含 202401 的进 202401 子目录），造几个不同名字的文件测试。
# 2. 写函数 find_duplicates(folder)：用文件大小（getsize）相同且文件名 stem 相同粗判重复并打印，不删除。
# 3. 综合挑战：把案例一到五封装成 organize(folder) 函数，返回报告 dict（分类数、总大小、是否无损），换一组测试数据完整跑一遍。
