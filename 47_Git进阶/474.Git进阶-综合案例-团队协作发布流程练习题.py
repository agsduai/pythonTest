# ===== 第474课：Git进阶-综合案例-团队协作发布流程 =====
# 知识点：
#   - 综合运用：分支（296）+ rebase（467）+ 压缩（468）+ cherry-pick（469）
#     + tag（297）+ reflog（471）
#   - 典型发布流程：feature 开发 → rebase 主干 → squash 合并 → 打 tag
#   - hotfix 流程：从 tag 拉修复分支 → 修复 → cherry-pick 回主干 → 补丁版本
#   - 原则：主干保持可发布；功能分支短生命周期；发布必须能追溯
import shutil
import stat
import subprocess
from pathlib import Path

DEMO = Path("git_demo_474")


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

# ---------------- 1. 初始版本 ----------------
(DEMO / "app.py").write_text("VERSION = '1.0'\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "chore: 初始版本")
git("tag", "-a", "v1.0.0", "-m", "首个正式版本")
main_branch = git("branch", "--show-current")
print("主干：", main_branch, "| 标签：", git("tag"))

# ---------------- 2. 功能分支开发 ----------------
print("\n== 功能分支：登录（2 个提交）==")
git("switch", "-c", "feature-login")
for i in (1, 2):
    (DEMO / "login.py").write_text(f"# 登录 v{i}\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", f"feat: 登录第 {i} 步")

# 主干同时前进
git("switch", main_branch)
(DEMO / "README.md").write_text("# 项目说明\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "docs: 补充 README")

print("\n== rebase 到最新主干 ==")
git("switch", "feature-login")
print(git("rebase", main_branch))

# ---------------- 3. squash 合并 ----------------
print("\n== squash 合并进主干 ==")
git("switch", main_branch)
print(git("merge", "--squash", "feature-login"))
git("commit", "-m", "feat: 登录功能（压缩为一个提交）")
print(git("log", "--oneline", "--graph", "-4"))

# ---------------- 4. 发布 v1.1.0 ----------------
print("\n== 发布 v1.1.0 ==")
(DEMO / "app.py").write_text("VERSION = '1.1'\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "chore: 版本号 1.1")
git("tag", "-a", "v1.1.0", "-m", "登录功能发布")
print("标签：", git("tag"))

# ---------------- 5. hotfix：从 tag 拉分支 ----------------
print("\n== hotfix：从 v1.1.0 拉修复分支 ==")
git("switch", "-c", "hotfix-1.1.1", "v1.1.0")
(DEMO / "login.py").write_text("# 登录（修复注入漏洞）\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "fix: 登录注入漏洞")
fix_hash = git("rev-parse", "HEAD")
print("修复提交：", fix_hash[:7])

# 把修复同步回主干
git("switch", main_branch)
print(git("cherry-pick", fix_hash))
git("tag", "-a", "v1.1.1", "-m", "安全补丁")

# ---------------- 6. 下一个功能 ----------------
print("\n== 下一个功能：搜索 ==")
git("switch", "-c", "feature-search")
(DEMO / "search.py").write_text("# 搜索功能\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "feat: 搜索")
git("switch", main_branch)
git("merge", "--no-ff", "feature-search", "-m", "merge: 搜索功能")
print(git("log", "--oneline", "--graph", "-6"))

# ---------------- 7. 发布检查 ----------------
print("\n== 发布检查清单 ==")
checks = {
    "主干历史": git("log", "--oneline").splitlines(),
    "标签": git("tag").splitlines(),
    "当前分支": git("branch", "--show-current"),
    "工作区干净": git("status", "--short") == "",
    "文件": sorted(p.name for p in DEMO.glob("*.py")),
}
for key, value in checks.items():
    if isinstance(value, list):
        print(f"  {key}：{len(value)} 项")
        for line in value[:5]:
            print("    ", line)
    else:
        print(f"  {key}：{value}")

print("\n== 分支列表 ==")
print(git("branch"))

# ---- 流程总结 ----
print("\n== 团队发布流程 ==")
for step in [
    "1. 从最新主干切 feature 分支（短生命周期）",
    "2. 小步提交，提交信息遵循 feat/fix/docs/chore",
    "3. 合并前 rebase 主干，解决冲突",
    "4. squash 合并，主干历史保持一条线",
    "5. 发布打 tag（附注标签 + 版本说明）",
    "6. 线上问题从 tag 拉 hotfix，修复后 cherry-pick 回主干",
    "7. 补丁版本号 +1，再打 tag",
]:
    print("  ", step)

force_rmtree(DEMO)

# ===== 练习题 =====
# 1. 在流程中加入“代码评审”分支保护的概念，说明哪些命令会被禁止。
# 2. 模拟两个功能分支同时开发，先后 rebase + squash 合并。
# 3. 用 git describe --tags 查看当前提交距离哪个 tag。
# 4. 思考：为什么发布必须从 tag 出发，而不是从“当时的主干 HEAD”出发？
