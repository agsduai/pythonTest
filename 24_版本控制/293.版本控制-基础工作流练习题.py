# ===== 第293课：版本控制-基础工作流 =====
# 知识点：
#   - 标准循环：改文件 → git add → git commit → 再改 → 再提交
#   - status --short 的字母含义：??未跟踪 / A新增暂存 / M已修改
#   - log --oneline 一行一条历史；show --stat 看提交改了哪些文件
#   - 每次提交都是一个“存档点”，可以随时回到这里

import shutil
import stat
import subprocess
from pathlib import Path

def force_rmtree(path):
    """删除含只读文件的目录：.git 的对象文件是只读的，普通 rmtree 删不掉。"""
    if not path.exists():
        return
    for p in path.rglob("*"):
        try:
            p.chmod(stat.S_IWRITE)
        except OSError:
            pass
    shutil.rmtree(path, ignore_errors=True)


DEMO = Path("git_demo_293")
force_rmtree(DEMO)
DEMO.mkdir()


def git(*args, cwd=DEMO, check=True):
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True,
        encoding="utf-8", errors="replace",
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 失败：\n{result.stderr}")
    return (result.stdout + result.stderr).strip()


git("init")
git("config", "user.name", "课程学员")
git("config", "user.email", "student@example.com")

# 1) 新文件：未跟踪
(DEMO / "app.py").write_text("print('v1')\n", encoding="utf-8")
print("新文件状态：", git("status", "--short"))          # ?? app.py

# 2) 暂存：进入“待提交购物车”
git("add", "app.py")
print("暂存后：", git("status", "--short"))              # A  app.py

# 3) 提交：生成第一个存档点
git("commit", "-m", "第一版")
print("历史：", git("log", "--oneline"))

# 4) 修改 → 再提交
(DEMO / "app.py").write_text("print('v2')\n", encoding="utf-8")
print("修改后：", git("status", "--short"))              # M app.py
git("add", ".")                                          # add . 表示全部暂存
git("commit", "-m", "第二版：修改输出")
print("两次提交：", git("log", "--oneline"), sep="\n")

# 5) 最新提交动了什么
print("最新提交明细：", git("show", "HEAD", "--stat"), sep="\n")

force_rmtree(DEMO)

# ===== 练习题 =====
# 1. 体会 add 的“购物车”作用：改两个文件，只 add 其中一个再提交，看结果。
# 2. 用 git show HEAD~1 看上一次提交的内容。
# 3. 思考：commit message 为什么要求“说清这次改动做了什么”？
