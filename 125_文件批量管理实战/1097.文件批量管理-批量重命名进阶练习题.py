# ===== 第1097课：文件批量管理-批量重命名进阶 =====
# 知识点：
#   - 批量重命名三件套：splitext 拆后缀、f-string 组新名、os.rename 落地
#   - 先 sorted() 再改名的顺序重要：乱序改名容易互相覆盖
#   - "两步改名法"防冲突：先全部加临时前缀，再统一改成最终名
#   - 实际场景：证件照编号、剧集集数补零（1.mp4 -> S01E01.mp4）

# 案例一：统一加前缀
import os
import shutil
import tempfile

work = tempfile.mkdtemp(prefix="py1097_")
docs = os.path.join(work, "文档")
os.makedirs(docs)
for name in ["第一章.md", "第二章.md", "第三章.md"]:
    open(os.path.join(docs, name), "w").write("内容")

prefix = "Python教程_"
for name in sorted(os.listdir(docs)):
    ext = os.path.splitext(name)[1]
    os.rename(os.path.join(docs, name), os.path.join(docs, f"{prefix}{name}"))
print(f"加前缀后：{sorted(os.listdir(docs))}")

# 案例二：序号补零重命名
# 场景：1.jpg、2.jpg ... 12.jpg 排序会乱（10 排在 2 前面），统一补零
photos = os.path.join(work, "照片")
os.makedirs(photos)
for i in [1, 2, 10, 11, 12]:
    open(os.path.join(photos, f"{i}.jpg"), "w").write("img")

for name in sorted(os.listdir(photos)):
    stem, ext = os.path.splitext(name)
    os.rename(os.path.join(photos, name), os.path.join(photos, f"P{int(stem):03d}{ext}"))
print(f"补零后（排序整齐）：{sorted(os.listdir(photos))}")

# 案例三：替换文件名中的字符串
# 场景：把"草稿"改成"终稿"
for name in sorted(os.listdir(docs)):
    if "第一章" in name:
        os.rename(os.path.join(docs, name), os.path.join(docs, name.replace("第一章", "第01章")))
print(f"替换后：{sorted(os.listdir(docs))}")

# 案例四：两步改名法 —— 防止 A 改成 B 时已有 B
# 场景：交换两个文件名 a.txt <-> b.txt，直接改名会冲突
swap = os.path.join(work, "交换")
os.makedirs(swap)
open(os.path.join(swap, "a.txt"), "w").write("A")
open(os.path.join(swap, "b.txt"), "w").write("B")

# 第一步：全部改成临时名
mapping = {"a.txt": "b.txt", "b.txt": "a.txt"}
for name in mapping:
    os.rename(os.path.join(swap, name), os.path.join(swap, f"__tmp_{name}"))
# 第二步：临时名改成最终名
for old, new in mapping.items():
    os.rename(os.path.join(swap, f"__tmp_{old}"), os.path.join(swap, new))
print(f"交换后内容：a.txt 是 '{open(os.path.join(swap, 'a.txt')).read()}'，b.txt 是 '{open(os.path.join(swap, 'b.txt')).read()}'")

# 收尾清理
shutil.rmtree(work)
print(f"临时目录已清理：{not os.path.exists(work)}")

# ===== 练习题 =====
# 1. 建 5 个 "ep1.mp4" ~ "ep5.mp4"，重命名为补零的 "EP01.mp4" ~ "EP05.mp4"，打印结果。
# 2. 写函数 add_suffix(folder, suffix)：给所有文件名在后缀前插入字符串（如 a.txt -> a_备份.txt），测试 3 个文件。
# 3. 综合挑战：写"预览模式"的批量改名函数 rename_plan(folder, func)：只打印"将改名 x -> y"不执行，确认合理后再传 apply=True 执行。
