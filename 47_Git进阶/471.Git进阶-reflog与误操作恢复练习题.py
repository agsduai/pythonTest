# ===== 第471课：Git进阶-reflog与误操作恢复 =====
# 知识点：
#   - reflog：HEAD 的移动日志，记录每一次切换/提交/重置（本地，默认保留 90 天）
#   - git reset --hard 之后，旧提交并没有立刻消失，reflog 里还能找到
#   - 恢复方式：git reset --hard <reflog 里的哈希>
#   - 删除的分支也能通过 reflog 找回：git branch <名字> <哈希>
#   - 这是 Git 的“后悔药”，但只对本地有效；push 出去的历史要靠 revert
import shutil
import stat
import subprocess
from pathlib import Path

DEMO = Path("git_demo_471")


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

# ---- 造三次提交 ----
for i in range(1, 4):
    (DEMO / "data.txt").write_text(f"版本 {i}\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", f"提交 {i}")
main_branch = git("branch", "--show-current")      # 先记住主分支名
print("== 当前历史 ==")
print(git("log", "--oneline"))
latest = git("rev-parse", "HEAD")
print("最新提交：", latest[:7])

# ---- 误操作：reset --hard 回到两次之前 ----
print("\n== 误操作：reset --hard HEAD~2 ==")
git("reset", "--hard", "HEAD~2")
print("  当前历史：", git("log", "--oneline"))
print("  文件内容：", (DEMO / "data.txt").read_text(encoding="utf-8").strip())

# ---- reflog 找到丢失的提交 ----
print("\n== git reflog（最近 6 条）==")
reflog = git("reflog", "--oneline", "-6")
print(reflog)

print("\n== 恢复：reset --hard 回到丢失的提交 ==")
git("reset", "--hard", latest)
print("  历史：", git("log", "--oneline"))
print("  文件内容：", (DEMO / "data.txt").read_text(encoding="utf-8").strip())

# ---- 找回被删除的分支 ----
print("\n== 删除分支后找回 ==")
git("switch", "-c", "temp-feature")
(DEMO / "temp.txt").write_text("临时分支的重要提交\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "temp: 重要改动")
temp_hash = git("rev-parse", "HEAD")
git("switch", main_branch)
git("branch", "-D", "temp-feature")
print("  删除后分支列表：", git("branch"))

# 从 reflog 找到 temp 的提交
reflog_all = git("reflog", "--all", "--oneline", "-12")
print("\n  reflog 中的相关记录：")
for line in reflog_all.splitlines():
    if "temp" in line or temp_hash[:7] in line:
        print("   ", line)

git("branch", "temp-feature", temp_hash)         # 用哈希重建分支
git("switch", "temp-feature")
print("\n  恢复后分支：", git("branch"))
print("  文件：", sorted(p.name for p in DEMO.glob("*.txt")))
print("  内容：", (DEMO / "temp.txt").read_text(encoding="utf-8").strip())

# ---- reflog 的边界 ----
print("\n== 使用边界 ==")
for item in [
    "reflog 只记录本地的 HEAD/分支移动，不会同步到远端",
    "gc 清理过期对象后，太久远的记录可能找不回",
    "reset --hard 前先 git stash 或建临时分支更稳",
    "已推送的历史不要 reset --hard 重写，用 revert（第295课）",
]:
    print("  -", item)

force_rmtree(DEMO)

# ===== 练习题 =====
# 1. 用 git reflog show <branch> 查看某分支的移动记录。
# 2. 模拟 rebase 中断后，用 reflog 回到 rebase 前的状态。
# 3. 给 reflog 记录设置过期时间（gc.reflogExpire），了解配置。
# 4. 思考：reflog 为什么不是“备份”？它不能恢复什么？
