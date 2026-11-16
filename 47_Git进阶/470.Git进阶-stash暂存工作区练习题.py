# ===== 第470课：Git进阶-stash暂存工作区 =====
# 知识点：
#   - stash：把“还没提交的改动”临时收起来，工作区恢复干净
#   - 场景：正在开发时被打断，要切分支修 bug；拉取远端前保存现场
#   - 默认只存已跟踪文件的改动；-u 连未跟踪文件一起存
#   - stash list / show / pop / apply / drop 的区分
#   - apply 保留 stash，pop = apply + drop
import shutil
import stat
import subprocess
from pathlib import Path

DEMO = Path("git_demo_470")


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

(DEMO / "app.py").write_text("print('v1')\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "base")
main_branch = git("branch", "--show-current")

# ---- 正在开发，突然要修 bug ----
print("== 开发中的工作区 ==")
(DEMO / "app.py").write_text("print('v2 开发中，未完成')\n", encoding="utf-8")
(DEMO / "note.txt").write_text("未跟踪的草稿\n", encoding="utf-8")
print("  状态：", git("status", "--short"))
print("  app.py：", (DEMO / "app.py").read_text(encoding="utf-8").strip())

# ---- 收起现场（包含未跟踪文件）----
print("\n== git stash push -u -m ==")
print(git("stash", "push", "-u", "-m", "登录功能开发中"))
print("  状态：", repr(git("status", "--short")))
print("  app.py 已恢复：", (DEMO / "app.py").read_text(encoding="utf-8").strip())
print("  note.txt 是否存在：", (DEMO / "note.txt").exists())

# ---- 查看 stash 列表与内容 ----
print("\n== stash 列表 ==")
print(git("stash", "list"))
print("\n== 查看某个 stash 的改动 ==")
print(git("stash", "show", "--stat", "stash@{0}"))

# ---- 去别的分支修 bug ----
print("\n== 切分支修 bug（工作区干净，不会带过去）==")
git("switch", "-c", "hotfix")
(DEMO / "bug.txt").write_text("修复说明\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "hotfix: 修复线上问题")
print("  hotfix 提交：", git("log", "--oneline", "-1"))
print("  工作区文件：", sorted(p.name for p in DEMO.iterdir() if p.is_file()))

# ---- 回到原分支恢复现场 ----
print("\n== 切回并恢复现场 ==")
git("switch", main_branch)
print(git("stash", "pop"))
print("  app.py：", (DEMO / "app.py").read_text(encoding="utf-8").strip())
print("  note.txt：", (DEMO / "note.txt").read_text(encoding="utf-8").strip())
print("  stash 列表（已空）：", repr(git("stash", "list")))

# ---- apply 与 pop 的区别 ----
print("\n== apply：恢复但保留 stash ==")
git("stash", "push", "-m", "第二个现场")
print(git("stash", "apply", "stash@{0}"))
print("  apply 后 stash 仍在：", git("stash", "list").splitlines()[0])
git("stash", "drop", "stash@{0}")               # 手动清理
print("  drop 后：", repr(git("stash", "list")))

# ---- 常见坑 ----
print("\n== 常见坑 ==")
for item in [
    "默认不存未跟踪文件 → 新文件会留在工作区，用 -u",
    "-u 也不包含 .gitignore 忽略的文件 → 需要 -a",
    "stash 不是备份：先确认 pop 成功再 drop",
    "冲突时 pop 失败但 stash 不会丢，解决后可重试",
    "stash 是本地栈，不会推送，也不会出现在 log 里",
]:
    print("  -", item)

force_rmtree(DEMO)

# ===== 练习题 =====
# 1. 用 git stash push -p 只暂存部分改动（交互式，了解即可）。
# 2. 制造 pop 冲突，解决后观察 stash 是否还在。
# 3. 用 git stash branch new-branch 从 stash 直接建分支。
# 4. 思考：stash 与临时 commit 相比，各适合什么场景？
