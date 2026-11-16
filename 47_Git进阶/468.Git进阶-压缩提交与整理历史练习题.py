# ===== 第468课：Git进阶-压缩提交与整理历史 =====
# 知识点：
#   - 提交信息写错/漏文件 → git commit --amend 修补最后一次提交
#   - 多个小提交合并成一个 → git reset --soft HEAD~n 后重新 commit
#   - 分支合并时压成一个提交 → git merge --squash
#   - 三者的共同点：让历史更可读，但都会改写提交（未推送前使用）
#   - 已推送的历史用 revert 而不是改写（第295课）
import shutil
import stat
import subprocess
from pathlib import Path

DEMO = Path("git_demo_468")


def force_rmtree(path: Path):
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

# ---------------- 1. amend：修补最后一次提交 ----------------
print("== 1. amend 修补提交信息 ==")
(DEMO / "app.py").write_text("print('v1')\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "第一版")
git("commit", "--amend", "-m", "第一版（补充说明）")
print(git("log", "--oneline", "-1"))

# 漏了文件也可以 amend 进同一个提交
(DEMO / "config.py").write_text("DEBUG = True\n", encoding="utf-8")
git("add", "config.py")
git("commit", "--amend", "--no-edit")          # 保持原提交信息
print("amend 后最新提交包含：")
print(git("show", "--stat", "--oneline", "HEAD"))

# ---------------- 2. reset --soft：多个提交压成一个 ----------------
print("\n== 2. 三个小提交压缩成一个 ==")
for i in range(1, 4):
    (DEMO / "app.py").write_text(f"print('v{i + 1}')\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", f"小改动 {i}")
print("压缩前：")
print(git("log", "--oneline"))

git("reset", "--soft", "HEAD~3")               # 撤销 3 次提交，改动回到暂存区
git("commit", "-m", "合并：三次小改动整理为一个功能提交")
print("\n压缩后：")
print(git("log", "--oneline"))

# ---------------- 3. merge --squash：分支压成一个提交 ----------------
print("\n== 3. merge --squash 合并分支 ==")
main_branch = git("branch", "--show-current")
git("switch", "-c", "feature")
for i in range(1, 3):
    (DEMO / f"feature_{i}.py").write_text(f"# 功能 {i}\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", f"feature 提交 {i}")

git("switch", main_branch)
print(git("merge", "--squash", "feature"))
git("commit", "-m", "合并 feature（2 个提交压缩为 1 个）")
print("\n最终历史：")
print(git("log", "--oneline", "--graph"))
print("\n文件：", sorted(p.name for p in DEMO.glob("*.py")))

# ---- 三种方式的选择 ----
print("\n== 使用场景 ==")
for item in [
    "amend：刚提交完就发现信息写错/漏文件",
    "reset --soft + commit：本地一串碎片提交要合并",
    "merge --squash：功能分支合并进主干时只留一个提交",
    "共同前提：这些提交还没有 push 到公共分支",
]:
    print("  -", item)

force_rmtree(DEMO)

# ===== 练习题 =====
# 1. 用 git commit --amend 修改作者邮箱，观察哈希变化。
# 2. 用 git rebase -i 的 squash 完成同样的压缩（了解交互式流程）。
# 3. 比较 merge --squash 与普通 merge 后的 git log --graph。
# 4. 思考：压缩提交会让“回滚到某个小改动”变难吗？
