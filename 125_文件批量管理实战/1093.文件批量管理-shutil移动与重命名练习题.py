# ===== 第1093课：文件批量管理-shutil移动与重命名 =====
# 知识点：
#   - shutil.move(源, 目标)：移动文件/目录，也可当作"重命名"用
#   - os.rename 同盘重命名更快；跨盘移动必须用 shutil.move
#   - 目标同名文件存在时：os.rename 报错（Windows），shutil.move 直接覆盖
#   - 实际场景：归档旧文件、按规则重命名截图/照片

# 案例一：移动文件到子目录
import shutil
import os
import tempfile

work = tempfile.mkdtemp(prefix="py1093_")
inbox = os.path.join(work, "收件箱")
archive = os.path.join(work, "归档")
os.makedirs(inbox)
os.makedirs(archive)
open(os.path.join(inbox, "发票.pdf"), "w").write("发票内容")

shutil.move(os.path.join(inbox, "发票.pdf"), os.path.join(archive, "发票.pdf"))
print(f"移动后收件箱：{os.listdir(inbox)}，归档：{os.listdir(archive)}")

# 案例二：移动并改名（一步到位）
open(os.path.join(inbox, "合同.docx"), "w").write("合同")
shutil.move(
    os.path.join(inbox, "合同.docx"),
    os.path.join(archive, "2024_合同.docx"),
)
print(f"移动改名后归档：{sorted(os.listdir(archive))}")

# 案例三：重命名 —— 同目录下 move 就是改名
old_name = os.path.join(archive, "2024_合同.docx")
new_name = os.path.join(archive, "2024_合同_最终版.docx")
shutil.move(old_name, new_name)
print(f"改名后：{os.listdir(archive)}")

# 案例四：批量重命名 —— 加日期前缀
# 场景：把下载文件夹里的图片统一加日期前缀
photos = os.path.join(work, "照片")
os.makedirs(photos)
for name in ["IMG_001.jpg", "IMG_002.jpg", "IMG_003.jpg"]:
    open(os.path.join(photos, name), "w").write("img")

date_prefix = "20240115_"
for name in sorted(os.listdir(photos)):
    src = os.path.join(photos, name)
    dst = os.path.join(photos, date_prefix + name)
    os.rename(src, dst)  # 同目录改名用 os.rename 即可
print(f"批量改名后：{sorted(os.listdir(photos))}")

# 案例五：按序号重命名 —— 一张一张编好号
for i, name in enumerate(sorted(os.listdir(photos)), start=1):
    ext = os.path.splitext(name)[1]
    os.rename(os.path.join(photos, name), os.path.join(photos, f"照片{i:03d}{ext}"))
print(f"编号后：{sorted(os.listdir(photos))}")

# 收尾清理
shutil.rmtree(work)
print(f"临时目录已清理：{not os.path.exists(work)}")

# ===== 练习题 =====
# 1. 在临时目录建 5 个文件，用 shutil.move 全部移入"已完成"子目录，打印移动前后文件数。
# 2. 写函数 batch_rename(folder, keyword, replacement)：把文件名中含 keyword 的部分替换掉，测试把 "temp_" 前缀去掉。
# 3. 综合题：把混杂目录里 .txt 移到 txt_dir、.jpg 移到 jpg_dir（遍历 + splitext 判断 + move），打印两个目录最终内容。
