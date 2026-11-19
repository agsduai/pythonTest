# ===== 第1098课：文件批量管理-zip打包与解压 =====
# 知识点：
#   - shutil.make_archive(基础名, "zip", root_dir=目录)：一键把目录打包成 zip
#   - shutil.unpack_archive(zip路径, 解压到目录)：一键解压
#   - zipfile 模块可"看包里有什么"：namelist() 列出全部条目
#   - 实际场景：备份项目、发给别人打包资料、下载包解压

# 案例一：打包整个目录
import shutil
import os
import tempfile
import zipfile

work = tempfile.mkdtemp(prefix="py1098_")
project = os.path.join(work, "我的项目")
os.makedirs(os.path.join(project, "数据"), exist_ok=True)
open(os.path.join(project, "main.py"), "w").write("print('hi')")
open(os.path.join(project, "数据", "sales.csv"), "w").write("month,amount\n1,100\n")

# make_archive 返回打包文件路径（自动加 .zip 后缀）
base = os.path.join(work, "项目备份")  # 不带 .zip
archive_path = shutil.make_archive(base, "zip", root_dir=project)
print(f"打包完成：{os.path.basename(archive_path)}，大小 {os.path.getsize(archive_path)} 字节")

# 案例二：查看包里有什么（不解压）
with zipfile.ZipFile(archive_path) as zf:
    names = zf.namelist()
    print(f"包内条目：{names}")
    print(f"文件数：{len([n for n in names if not n.endswith('/')])}")

# 案例三：解压到指定目录
restore_dir = os.path.join(work, "还原")
os.makedirs(restore_dir)
shutil.unpack_archive(archive_path, restore_dir)
# 打包时的 root_dir 是 project 本身，所以解压出来直接就是项目内容
restored_files = []
for root, dirs, files in os.walk(restore_dir):
    for name in files:
        restored_files.append(os.path.relpath(os.path.join(root, name), restore_dir))
print(f"解压还原：{sorted(restored_files)}")
print(f"内容一致：{open(os.path.join(restore_dir, '数据', 'sales.csv'), encoding='utf-8').read().startswith('month')}")

# 案例四：只打包指定文件（zipfile 手动打包）
# 场景：项目里只发 .py 文件给别人
handover = os.path.join(work, "交付包")
os.makedirs(handover)
zip_path = shutil.make_archive(os.path.join(work, "tmp_full"), "zip", root_dir=project)
# 手动重打包：只挑 .py
with zipfile.ZipFile(zip_path) as src, zipfile.ZipFile(os.path.join(handover, "交付.zip"), "w") as dst:
    for info in src.infolist():
        if info.filename.endswith(".py"):
            dst.writestr(info, src.read(info.filename))
with zipfile.ZipFile(os.path.join(handover, "交付.zip")) as zf:
    print(f"交付包内容（只有 .py）：{zf.namelist()}")

# 收尾清理
shutil.rmtree(work)
print(f"临时目录已清理：{not os.path.exists(work)}")

# ===== 练习题 =====
# 1. 把含 3 个文件的目录打包成 zip，打印包内文件数与 zip 大小，再解压验证文件都在。
# 2. 写函数 backup_folder(folder, backup_dir)：每次备份生成带日期时间的 zip 名（如 备份_20240115_0930.zip，用 strftime('%Y%m%d_%H%M%S')），连续调两次生成两个包、互不覆盖。
# 3. 综合挑战：用 zipfile 读取一个 zip，打印每个文件的文件名和 compress_size，并输出压缩率最大的文件名。
