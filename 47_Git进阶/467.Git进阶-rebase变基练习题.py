# ===== 第467课：Git进阶-rebase变基 =====
# 知识点：
#   - rebase：把当前分支的提交“搬”到另一个分支的最新提交之后，历史变成一条直线
#   - merge 会保留分叉并产生合并提交；rebase 会重写提交（哈希变化）
#   - 典型用法：功能分支开发期间主分支前进，合并前先 rebase 到最新 main
#   - 黄金法则：不要 rebase 已经推送到公共分支的提交（会改写别人的历史）
#   - 本课在临时仓库演示，不影响真实项目（同第24章）
import shutil
import stat
import subprocess
from pathlib import Path

DEMO = Path("git_demo_467")


def force_rmtree(path: Path):
    """删除含只读文件的目录（.git 对象文件是只读的）。"""
    if not path.exists():
        return
    for p in path.rglob("*"):
        try:
            p.chmod(stat.S_IWRITE)
        except OSError:
            pass
    shutil.rmtree(path, ignore_errors=True)


def git(*args, cwd=DEMO, check=True):
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True,
        encoding="utf-8", errors="replace",
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 失败：\n{result.stderr}")
    return (result.stdout + result.stderr).strip()


force_rmtree(DEMO)
DEMO.mkdir()
git("init")
git("config", "user.name", "课程学员")
git("config", "user.email", "student@example.com")

(DEMO / "app.py").write_text("print('base')\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "base")
main_branch = git("branch", "--show-current")
print("主分支：", main_branch)

# ---- 功能分支开发 ----
git("switch", "-c", "feature")
(DEMO / "login.py").write_text("# 登录功能 v1\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "feature: 登录 v1")
(DEMO / "login.py").write_text("# 登录功能 v2\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "feature: 登录 v2")

# ---- 主分支同时前进 ----
git("switch", main_branch)
(DEMO / "main.py").write_text("# 主分支新功能\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "main: 新功能")

print("\n== rebase 前：历史分叉 ==")
print(git("log", "--oneline", "--graph", "--all"))
print("  feature 的基点：", git("merge-base", main_branch, "feature")[:7])

# ---- rebase：把 feature 的提交搬到 main 之后 ----
git("switch", "feature")
print("\n== 执行 rebase ==")
print(git("rebase", main_branch))
print("\n== rebase 后：历史变成直线 ==")
print(git("log", "--oneline", "--graph", "--all"))

# ---- 验证：功能与主分支文件都在 ----
print("\n== 文件检查 ==")
print("  feature 分支文件：", sorted(p.name for p in DEMO.glob("*.py")))
print("  app.py 内容：", (DEMO / "app.py").read_text(encoding="utf-8").strip())
print("  login.py 内容：", (DEMO / "login.py").read_text(encoding="utf-8").strip())

# ---- 对比：merge 的做法 ----
print("\n== merge 与 rebase 的差异 ==")
for item in [
    "merge：保留分叉，多一个合并提交，历史真实但较乱",
    "rebase：提交被复制到新基点，历史线性，但哈希全变",
    "团队规范：功能分支合并前 rebase；公共分支禁止 rebase",
    "冲突处理：rebase 过程中逐个提交解决；merge 一次性解决",
]:
    print("  -", item)

force_rmtree(DEMO)

# ===== 练习题 =====
# 1. 在 rebase 前制造同一文件冲突，解决后继续（git rebase --continue）。
# 2. 用 git rebase --abort 体验中途取消。
# 3. 对比同一组提交 merge 与 rebase 后的 git log --graph。
# 4. 思考：为什么“已经 push 的分支不要 rebase”？
