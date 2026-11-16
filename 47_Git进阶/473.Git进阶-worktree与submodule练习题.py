# ===== 第473课：Git进阶-worktree与submodule =====
# 知识点：
#   - worktree：同一个仓库检出多个工作目录，各自在不同分支上
#   - 场景：一边在 main 上修 bug，一边保留 feature 的开发现场，不用 stash
#   - git worktree add/list/remove；多个工作区共享同一个 .git 版本库
#   - submodule：把一个 Git 仓库作为另一个仓库的子目录（固定到某个提交）
#   - 常用命令：submodule add/status/update；clone 时要 --recurse-submodules
#   - 注意：submodule 容易“版本漂移”，团队要约定更新流程
import shutil
import stat
import subprocess
from pathlib import Path

DEMO = Path("git_demo_473")
WT = Path("git_demo_473_wt")
LIB = Path("git_demo_473_lib")


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


for p in (DEMO, WT, LIB):
    force_rmtree(p)

# ---------------- 1. worktree ----------------
DEMO.mkdir()
git("init")
git("config", "user.name", "课程学员")
git("config", "user.email", "student@example.com")
(DEMO / "app.py").write_text("print('v1')\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "base")
main_branch = git("branch", "--show-current")

print("== 创建第二个工作区（hotfix 分支）==")
print(git("worktree", "add", str(WT.resolve()), "-b", "hotfix"))
print("工作区列表：")
print(git("worktree", "list"))

# ---- 在 WT 里修 bug，DEMO 不受影响 ----
print("\n== 在 WT 里提交修复 ==")
(WT / "app.py").write_text("print('v1 + hotfix')\n", encoding="utf-8")
result = subprocess.run(["git", "add", "."], cwd=WT, capture_output=True, encoding="utf-8")
result = subprocess.run(["git", "commit", "-m", "hotfix: 修复"], cwd=WT,
                        capture_output=True, encoding="utf-8", errors="replace")
print("  commit 输出：", (result.stdout + result.stderr).strip().splitlines()[0])
print("  DEMO 的 app.py：", (DEMO / "app.py").read_text(encoding="utf-8").strip())
print("  WT 的 app.py：", (WT / "app.py").read_text(encoding="utf-8").strip())

# ---- 合并修复，移除 worktree ----
print("\n== 在 DEMO 合并 hotfix 并移除 worktree ==")
git("merge", "hotfix")
print("  main 的 app.py：", (DEMO / "app.py").read_text(encoding="utf-8").strip())
print(git("worktree", "remove", str(WT.resolve()), "--force"))
print("  剩余工作区：")
print(git("worktree", "list"))

# ---------------- 2. submodule ----------------
print("\n== submodule：把 LIB 作为子模块 ==")
LIB.mkdir()
subprocess.run(["git", "init"], cwd=LIB, capture_output=True)
subprocess.run(["git", "config", "user.name", "课程学员"], cwd=LIB, capture_output=True)
subprocess.run(["git", "config", "user.email", "student@example.com"], cwd=LIB, capture_output=True)
(LIB / "utils.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
subprocess.run(["git", "add", "."], cwd=LIB, capture_output=True)
subprocess.run(["git", "commit", "-m", "lib v1"], cwd=LIB, capture_output=True)

try:
    out = git("-c", "protocol.file.allow=always", "submodule", "add",
              str(LIB.resolve()), "libs/util", check=False)
    print("  add 输出：", out.splitlines()[0] if out else "（无输出）")
    git("commit", "-m", "引入 util 子模块")
    print("\n  submodule 状态：")
    print(git("submodule", "status"))
    print("  子模块目录：", sorted(p.name for p in (DEMO / "libs" / "util").iterdir()
                                  if p.name != ".git"))
    print("  .gitmodules：")
    print((DEMO / ".gitmodules").read_text(encoding="utf-8"))
except Exception as exc:
    print("  submodule 演示被环境限制：", exc)
    print("  （这本身也是一个常见问题：文件协议默认被禁，需要 protocol.file.allow）")

# ---- 管理建议 ----
print("\n== 使用建议 ==")
for item in [
    "worktree：同时开多个分支的编辑窗口，共享对象库、省磁盘",
    "worktree 不要放在仓库内部，避免被误提交",
    "submodule：第三方库需要固定版本时使用",
    "submodule 更新要显式提交父仓库的指针变化",
    "clone 带子模块：git clone --recurse-submodules <url>",
]:
    print("  -", item)

for p in (DEMO, WT, LIB):
    force_rmtree(p)

# ===== 练习题 =====
# 1. 用 worktree 同时检出 main 与 release 分支，各改一个文件互不影响。
# 2. 在子模块里提交新版本，回到父仓库观察 git status 的变化。
# 3. 用 git submodule update --remote 更新子模块到最新。
# 4. 思考：什么时候该用 submodule，什么时候该用包管理器（pip）？
