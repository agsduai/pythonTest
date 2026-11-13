# ===== 第294课：版本控制-查看历史与差异 =====
# 知识点：
#   - diff 三对照：工作区 vs 暂存区 / 暂存区 vs 最新提交 / 提交 vs 提交
#   - git diff 默认对比“工作区 vs 暂存区”；--cached 对比“暂存区 vs HEAD”
#   - log -p：每条历史附上具体改动；HEAD / HEAD~1 是提交的“坐标”

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


DEMO = Path("git_demo_294")
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

# 两个历史版本
(DEMO / "app.py").write_text("print('v1')\nprint('end')\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "v1")
(DEMO / "app.py").write_text("print('v2')\nprint('end')\nprint('new feature')\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "v2")

# ---- 工作区再改一行（未暂存）----
(DEMO / "app.py").write_text("print('v2-work')\nprint('end')\nprint('new feature')\n", encoding="utf-8")
print("状态（M=已修改未暂存）：", git("status", "--short"))
print("工作区 vs 暂存区：", git("diff"), sep="\n")

# ---- 暂存后再看：diff 变空，--cached 有内容 ----
git("add", ".")
print("暂存后 diff（空）：", repr(git("diff")))
print("暂存区 vs 最新提交：", git("diff", "--cached"), sep="\n")

# ---- 提交之间的对比 ----
git("commit", "-m", "v2-work")
print("两次提交对比：", git("diff", "HEAD~1", "HEAD"), sep="\n")

# ---- log -p：历史+改动一起看 ----
print("最近一次提交的改动：", git("log", "-p", "-1"), sep="\n")

force_rmtree(DEMO)

# ===== 练习题 =====
# 1. 制造“改了两处只暂存一处”的状态，分别看 diff 与 diff --cached。
# 2. 用 log --oneline --graph 看历史（本课是直线，下一课分支后就有分叉了）。
# 3. 思考：diff 的 - + 号各代表什么？
