# ===== 第1010课：综合小项目实战-文件分类器 =====
# 知识点：
#   - os.listdir 列出文件，os.path.splitext 获取后缀
#   - 后缀 → 目标目录的映射字典
#   - os.makedirs + os.rename 实现自动归类
#   - 实际场景：整理下载文件夹——把混杂的文件按类型分目录存放
# 依赖：无（标准库）
import os
import shutil

TARGET_DIR = "分类测试"

# 后缀 → 分类目录名的映射
CATEGORY_MAP = {
    ".jpg": "图片", ".png": "图片", ".gif": "图片",
    ".mp4": "视频", ".avi": "视频",
    ".mp3": "音频", ".wav": "音频",
    ".pdf": "文档", ".docx": "文档", ".txt": "文档",
    ".py": "代码", ".html": "代码",
}


def get_category(filename):
    """根据文件后缀返回分类目录名。"""
    ext = os.path.splitext(filename)[1].lower()
    return CATEGORY_MAP.get(ext, "其他")


def create_test_files(directory):
    """创建测试文件。"""
    os.makedirs(directory, exist_ok=True)
    test_files = [
        "photo1.jpg", "photo2.png", "movie.mp4",
        "report.pdf", "notes.txt", "script.py",
        "song.mp3", "unknown.xyz",
    ]
    for name in test_files:
        path = os.path.join(directory, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"{name} 的内容")
    return test_files


def classify_files(directory):
    """按类型分目录存放文件。返回分类统计。"""
    categories = {}
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if not os.path.isfile(filepath):
            continue
        category = get_category(filename)
        category_dir = os.path.join(directory, category)
        os.makedirs(category_dir, exist_ok=True)
        # 移动文件
        new_path = os.path.join(category_dir, filename)
        shutil.move(filepath, new_path)
        categories.setdefault(category, []).append(filename)
    return categories


print("== 文件分类器 ==")
print(f"  目标目录: {TARGET_DIR}")

# 创建测试文件
test_files = create_test_files(TARGET_DIR)
print(f"\n  创建 {len(test_files)} 个测试文件:")
for name in test_files:
    print(f"    {name}")

print(f"\n  分类前的目录内容:")
for entry in sorted(os.listdir(TARGET_DIR)):
    print(f"    {entry}")

# 执行分类
print(f"\n== 执行分类 ==")
result = classify_files(TARGET_DIR)
for category, files in sorted(result.items()):
    print(f"  [{category}] -> {files}")

# 查看分类结果
print(f"\n== 分类后的目录结构 ==")
for entry in sorted(os.listdir(TARGET_DIR)):
    full = os.path.join(TARGET_DIR, entry)
    if os.path.isdir(full):
        files_in = os.listdir(full)
        print(f"  {entry}/ -> {files_in}")
    else:
        print(f"  {entry} (未分类)")

# 清理测试目录
shutil.rmtree(TARGET_DIR)
print(f"\n  清理测试目录: {not os.path.exists(TARGET_DIR)}")

print("\n== 扩展思考 ==")
for line in (
    "  分类映射表可以放到配置文件中，用户自定义分类规则",
    "  未知后缀统一放「其他」目录，而不是直接丢弃",
    "  重名文件处理：同名加序号后缀 (photo_1.jpg)",
    "  生产级工具还可以：递归子目录、按修改日期分类、去重",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 修改分类器：未识别后缀的文件归入「其他」目录（本课已实现，验证效果）。
# 2. 增加「按日期分类」模式：把文件按修改年份分目录。
# 3. 实现「重名处理」：目标目录已有同名文件时自动加序号。
# 4. 思考：shutil.move 和 os.rename 有什么区别？跨磁盘移动应该用哪个？
