# ===== 第1094课：文件批量管理-删除与安全检查 =====
# 知识点：
#   - os.remove 删文件；os.rmdir 只能删"空目录"；shutil.rmtree 删整棵目录树
#   - 删除不可恢复，动手前必须检查：路径存在吗？是不是要删的那个？
#   - 安全习惯：先 listdir 打印将要删除的内容，确认后再删
#   - ignore_errors=True 让 rmtree 遇到只读文件也不中断（慎用）

# 案例一：删文件与删空目录
import os
import shutil
import tempfile

work = tempfile.mkdtemp(prefix="py1094_")
f = os.path.join(work, "临时文件.txt")
open(f, "w").write("待删除")
os.remove(f)
print(f"文件删除成功：{not os.path.exists(f)}")

empty_dir = os.path.join(work, "空目录")
os.makedirs(empty_dir)
os.rmdir(empty_dir)  # 只能删空目录
print(f"空目录删除成功：{not os.path.exists(empty_dir)}")

# 案例二：rmtree 删除非空目录
# 场景：清理整个缓存目录
cache = os.path.join(work, "缓存")
os.makedirs(os.path.join(cache, "子目录"), exist_ok=True)
open(os.path.join(cache, "a.tmp"), "w").write("x")
open(os.path.join(cache, "子目录", "b.tmp"), "w").write("y")

# 安全习惯：删除前先看一眼里面有什么
print(f"将删除：{cache}，包含 {sum(len(fs) for _, _, fs in os.walk(cache))} 个文件")
shutil.rmtree(cache)
print(f"目录树删除成功：{not os.path.exists(cache)}")

# 案例三：安全删除函数 —— 检查再删
def safe_rmtree(path, confirm_keyword):
    """只有路径名包含确认关键词才允许删除。"""
    if not os.path.exists(path):
        print(f"{path} 不存在，无需删除")
        return False
    if confirm_keyword not in os.path.basename(path):
        print(f"路径名不含 '{confirm_keyword}'，拒绝删除（安全拦截）")
        return False
    shutil.rmtree(path)
    print(f"已删除：{path}")
    return True

target = os.path.join(work, "临时缓存_02")
os.makedirs(target)
safe_rmtree(target, "临时缓存")     # 名字匹配，允许删
safe_rmtree(target, "临时缓存")     # 已经不存在
safe_rmtree(work, "绝不存在的关键词")  # 名字不匹配，拦截

# 案例四：只删指定类型的文件
# 场景：清理目录里所有 .tmp 文件，保留其他
mix = os.path.join(work, "混合目录")
os.makedirs(mix)
for name in ["a.tmp", "b.tmp", "重要文档.txt", "c.tmp"]:
    open(os.path.join(mix, name), "w").write("x")

removed = 0
for name in os.listdir(mix):
    if name.endswith(".tmp"):
        os.remove(os.path.join(mix, name))
        removed += 1
print(f"删除 {removed} 个 .tmp，剩余：{os.listdir(mix)}")

# 收尾清理
shutil.rmtree(work)
print(f"临时目录已清理：{not os.path.exists(work)}")

# ===== 练习题 =====
# 1. 在临时目录建两层目录树（含 3 个文件），先打印树内容再 rmtree 删除，验证已删除。
# 2. 写函数 clean_empty_dirs(root)：找出 root 下所有空目录并 os.rmdir 删除，返回删除个数（提示：遍历后用反向排序删子目录）。
# 3. 综合题：给 safe_rmtree 增加"二次确认"——打印将删除的文件列表后，只有传入 confirm=True 才真正执行，分别测试确认与不确认两种调用。
