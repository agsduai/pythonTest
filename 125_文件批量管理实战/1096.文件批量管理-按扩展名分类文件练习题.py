# ===== 第1096课：文件批量管理-按扩展名分类文件 =====
# 知识点：
#   - 分类套路：遍历目录 -> splitext 取扩展名 -> 建目标目录 -> shutil.move
#   - os.path.splitext("a.tar.gz") 只切最后一个点 -> (".tar", ".gz")，注意复合后缀
#   - 扩展名统一小写比较：".JPG" 和 ".jpg" 是同类
#   - 同名冲突处理：目标已有同名文件时加序号再移

# 案例一：基础分类
import os
import shutil
import tempfile

work = tempfile.mkdtemp(prefix="py1096_")
messy = os.path.join(work, "下载文件夹")
os.makedirs(messy)
files = ["报告.docx", "照片1.jpg", "歌曲.mp3", "表格.xlsx", "照片2.JPG", "音乐.flac"]
for name in files:
    open(os.path.join(messy, name), "w").write("x")

# 按扩展名归类：图片 / 文档 / 音乐
rules = {".jpg": "图片", ".jpeg": "图片", ".png": "图片",
         ".docx": "文档", ".xlsx": "文档",
         ".mp3": "音乐", ".flac": "音乐"}

for name in os.listdir(messy):
    path = os.path.join(messy, name)
    if not os.path.isfile(path):
        continue  # 跳过子目录
    ext = os.path.splitext(name)[1].lower()  # 统一小写再匹配
    folder = rules.get(ext, "其他")
    target_dir = os.path.join(messy, folder)
    os.makedirs(target_dir, exist_ok=True)
    shutil.move(path, os.path.join(target_dir, name))

for folder in sorted(os.listdir(messy)):
    sub = os.path.join(messy, folder)
    if os.path.isdir(sub):
        print(f"{folder}/：{sorted(os.listdir(sub))}")

# 案例二：同名冲突处理
# 场景：两个文件同名（不同来源），移动时第二个自动加序号
src_dir = os.path.join(work, "来源")
img_dir = os.path.join(work, "相册")
os.makedirs(src_dir)
os.makedirs(img_dir)
open(os.path.join(img_dir, "IMG.jpg"), "w").write("旧")
open(os.path.join(src_dir, "IMG.jpg"), "w").write("新")

def move_no_overwrite(src, dst_dir):
    name = os.path.basename(src)
    dst = os.path.join(dst_dir, name)
    if os.path.exists(dst):
        stem, ext = os.path.splitext(name)
        i = 1
        while os.path.exists(dst):  # 一直找到空位
            dst = os.path.join(dst_dir, f"{stem}_{i}{ext}")
            i += 1
    shutil.move(src, dst)
    return os.path.basename(dst)

final_name = move_no_overwrite(os.path.join(src_dir, "IMG.jpg"), img_dir)
print(f"冲突自动改名：IMG.jpg -> {final_name}，相册内容：{sorted(os.listdir(img_dir))}")

# 收尾清理
shutil.rmtree(work)
print(f"临时目录已清理：{not os.path.exists(work)}")

# ===== 练习题 =====
# 1. 建一个混有 .py/.txt/.csv 的目录，按扩展名分进三个子目录，打印分类结果。
# 2. 修改案例一：把规则表换成"未匹配扩展名的文件留在原地"，再自行造一个"未知.zip"放入目录，验证它没被移动。
# 3. 综合挑战：写函数 classify(folder, rules)：返回分类统计 {文件夹: 数量}，并用它统计案例一目录中每类的文件数。
