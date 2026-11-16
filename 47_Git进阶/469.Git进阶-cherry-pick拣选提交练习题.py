# ===== 第469课：Git进阶-cherry-pick拣选提交 =====
# 知识点：
#   - cherry-pick：把“某一次提交的改动”摘到当前分支，生成一个新提交
#   - 场景：只想要功能分支里的一个修复；把 hotfix 同步到多个分支
#   - 与 merge/rebase 的区别：只取一个提交，不带上它的祖先
#   - 冲突处理：和普通合并一样，解决后 git cherry-pick --continue
#   - 注意：重复 cherry-pick 同一提交会产生重复改动（哈希不同）
import shutil
import stat
import subprocess
from pathlib import Path

DEMO = Path("git_demo_469")


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

(DEMO / "app.py").write_text("print('base')\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "base")
main_branch = git("branch", "--show-current")

# ---- 功能分支上三次提交 ----
git("switch", "-c", "feature")
(DEMO / "c1.py").write_text("# 功能 1\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "feature: 功能1")
(DEMO / "c2.py").write_text("# 紧急修复\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "feature: 紧急修复")
(DEMO / "c3.py").write_text("# 功能 2\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "feature: 功能2")

print("== 功能分支历史 ==")
print(git("log", "--oneline"))

# ---- 只摘取“紧急修复”那一个提交 ----
fix_hash = git("rev-parse", "feature~1")       # c3 的父提交 = 紧急修复
print("\n要摘取的提交：", fix_hash[:7], "feature: 紧急修复")

git("switch", main_branch)
print("\n== 在 main 上 cherry-pick ==")
print(git("cherry-pick", fix_hash))

print("\n== main 的历史 ==")
print(git("log", "--oneline"))
print("\n== main 的文件 ==")
print("  ", sorted(p.name for p in DEMO.glob("*.py")))
print("  说明：只带过来 c2.py，c1/c3 仍在 feature 分支")

# ---- 再次 cherry-pick 同一个提交 ----
print("\n== 重复 cherry-pick（会产生重复改动）==")
result = git("cherry-pick", fix_hash, check=False)
print("  ", result.splitlines()[0] if result else "（无输出）")
git("cherry-pick", "--quit", check=False)      # 清理“空拣选”状态，避免后续切分支报错
print("  历史：", git("log", "--oneline").splitlines()[:3])

# ---- 冲突演示：两边改同一行 ----
print("\n== 冲突演示 ==")
git("switch", "-c", "hotfix", "HEAD~1")
(DEMO / "app.py").write_text("print('hotfix 修复')\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "hotfix: 改 app.py")
hotfix_hash = git("rev-parse", "HEAD")

git("switch", main_branch)
(DEMO / "app.py").write_text("print('main 也改了')\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "main: 改 app.py")

conflict = git("cherry-pick", hotfix_hash, check=False)
print("  cherry-pick 结果：", conflict.splitlines()[0] if conflict else "")
print("  状态：", git("status", "--short"))

# 解决冲突：采用 hotfix 的内容
(DEMO / "app.py").write_text("print('hotfix 修复')\n", encoding="utf-8")
git("add", "app.py")
git("cherry-pick", "--continue")
print("  解决后 app.py：", (DEMO / "app.py").read_text(encoding="utf-8").strip())
print("  最终历史：", git("log", "--oneline").splitlines()[:3])

force_rmtree(DEMO)

# ---- 使用建议 ----
print("\n== 使用建议 ==")
for item in [
    "hotfix 同步：修复一个 bug → cherry-pick 到 release/主干",
    "只取部分功能：feature 里只想上线一个改动",
    "不要用 cherry-pick 代替 merge：它会复制提交，长期同步会乱",
    "记录来源：在提交信息里写清 cherry-pick 自哪个提交",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 用 git cherry-pick A..B 一次摘取一段连续提交。
# 2. 冲突时用 git cherry-pick --abort 放弃，观察状态恢复。
# 3. 对比 cherry-pick 与 rebase --onto 的适用场景。
# 4. 思考：为什么 cherry-pick 后两个分支的同一改动会有不同哈希？
