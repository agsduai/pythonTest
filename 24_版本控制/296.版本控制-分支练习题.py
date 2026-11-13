# ===== 第296课：版本控制-分支 =====
# 知识点：
#   - 分支：平行开发的“平行世界”，互不干扰，最后合并
#   - switch -c 建并切换；merge 把分支成果并回来
#   - 冲突：两个分支改了同一处 → git 标出冲突，人工决定后提交
#   - 团队习惯：main 保持稳定，功能在 feature 分支上开发

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


DEMO = Path("git_demo_296")
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
(DEMO / "app.py").write_text("功能 = 基础版\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "基础版")
main_branch = git("branch", "--show-current")     # master 或 main，看本机配置
print("当前分支：", main_branch)

# ---- 功能分支上开发 ----
git("switch", "-c", "feature-login")
(DEMO / "app.py").write_text("功能 = 基础版 + 登录\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "新增登录功能")
git("switch", main_branch)
print("切回主分支（没有登录功能）：", (DEMO / "app.py").read_text(encoding="utf-8").strip())

# ---- 合并：功能进入主线 ----
git("merge", "feature-login")
print("合并后：", (DEMO / "app.py").read_text(encoding="utf-8").strip())
print("历史图：", git("log", "--oneline", "--graph"), sep="\n")

# ---- 制造冲突：两个分支改同一行 ----
git("switch", "-c", "b1")
(DEMO / "app.py").write_text("标题 = 来自b1\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "b1 改标题")
git("switch", main_branch)
git("switch", "-c", "b2")
(DEMO / "app.py").write_text("标题 = 来自b2\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "b2 改标题")
git("switch", main_branch)

git("merge", "b1")                       # 先并 b1：顺利
conflict = git("merge", "b2", check=False)
print("合并 b2 发生冲突：", conflict.splitlines()[0] if conflict else "")
print("冲突状态：", git("status", "--short"))     # UU app.py

# ---- 解决冲突：人工决定内容，再提交 ----
(DEMO / "app.py").write_text("标题 = b1和b2商量后的结果\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "解决标题冲突")
print("解决后：", (DEMO / "app.py").read_text(encoding="utf-8").strip())

force_rmtree(DEMO)

# ===== 练习题 =====
# 1. 在 feature 分支上新增一个文件，合并后验证主分支也有它。
# 2. 制造“两分支各加不同内容到文件末尾”的合并 —— 这类冲突 git 能自动解决吗？
# 3. 思考：为什么冲突要人工解决，git 不敢自动选一边？
