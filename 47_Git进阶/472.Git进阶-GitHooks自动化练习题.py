# ===== 第472课：Git进阶-Git Hooks自动化 =====
# 知识点：
#   - Git Hooks：在提交/推送等时机自动执行的脚本，位于 .git/hooks/
#   - pre-commit：提交前检查（代码格式、敏感信息、单元测试）
#   - commit-msg：校验提交信息格式（如必须带任务号）
#   - pre-push：推送前跑更重的检查（全量测试）
#   - 钩子返回非 0 会阻止操作；本地钩子不会随 clone 分发（需 husky/pre-commit 框架）
#   - 本课在临时仓库演示，不影响真实项目
import os
import shutil
import stat
import subprocess
from pathlib import Path

DEMO = Path("git_demo_472")


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

# ---- 安装 pre-commit 钩子：阻止提交包含 BAD 的改动 ----
hook = DEMO / ".git" / "hooks" / "pre-commit"
hook.write_text(
    "#!/bin/sh\n"
    "echo '[pre-commit] 检查暂存区内容...'\n"
    "if git diff --cached | grep -q 'BAD'; then\n"
    "  echo '[pre-commit] 发现 BAD，提交被拦截'\n"
    "  exit 1\n"
    "fi\n"
    "echo '[pre-commit] 检查通过'\n"
    "exit 0\n",
    encoding="utf-8",
)
os.chmod(hook, 0o755)
print("已安装 pre-commit 钩子：", hook)

# ---- 提交包含禁用内容：被拦截 ----
print("\n== 提交包含 BAD 的改动 ==")
(DEMO / "bad.py").write_text("# BAD: 这是不允许提交的内容\n", encoding="utf-8")
git("add", "bad.py")
result = git("commit", "-m", "尝试提交坏内容", check=False)
print(result)
print("提交是否成功：", "提交被拦截" not in result)

# ---- 修正后提交：通过 ----
print("\n== 修正后再提交 ==")
(DEMO / "bad.py").write_text("# 已修正\n", encoding="utf-8")
git("add", "bad.py")
result = git("commit", "-m", "提交修正后的内容", check=False)
print(result)
print("历史：", git("log", "--oneline"))

# ---- commit-msg 钩子：校验提交信息格式 ----
print("\n== commit-msg 钩子：要求提交信息以 feat/fix/docs 开头 ==")
msg_hook = DEMO / ".git" / "hooks" / "commit-msg"
msg_hook.write_text(
    "#!/bin/sh\n"
    "msg=$(head -n 1 \"$1\")\n"
    "case \"$msg\" in\n"
    "  feat*|fix*|docs*|chore*) exit 0 ;;\n"
    "  *) echo \"提交信息必须以 feat/fix/docs/chore 开头：$msg\"; exit 1 ;;\n"
    "esac\n",
    encoding="utf-8",
)
os.chmod(msg_hook, 0o755)

print("  提交信息 '更新代码'：")
(DEMO / "x.txt").write_text("x", encoding="utf-8")
git("add", "x.txt")
print(git("commit", "-m", "更新代码", check=False))
print("  提交信息 'fix: 修复问题'：")
print(git("commit", "-m", "fix: 修复问题", check=False))
print("  历史：", git("log", "--oneline"))

# ---- 钩子分发：团队如何共享 ----
print("\n== 钩子共享方案 ==")
for item in [
    "把钩子脚本放进仓库（如 scripts/hooks/），用 core.hooksPath 指向它",
    "git config core.hooksPath scripts/hooks",
    "或用 pre-commit 框架（Python 生态的钩子管理器）",
    "CI 里也要跑同样的检查，不能只依赖本地钩子",
    "敏感信息扫描（密钥/密码）是 pre-commit 的高价值用法",
]:
    print("  -", item)

print("\n== 其他常用钩子 ==")
for name, desc in [
    ("pre-push", "推送前跑全量测试/构建"),
    ("post-commit", "提交后通知/记录（不能阻止提交）"),
    ("pre-rebase", "rebase 前检查是否已推送"),
]:
    print(f"  {name:14s} {desc}")

force_rmtree(DEMO)

# ===== 练习题 =====
# 1. 写一个 pre-commit 钩子：对暂存的 .py 文件跑 python -m py_compile。
# 2. 写一个 commit-msg 钩子：要求提交信息长度 >= 10。
# 3. 用 core.hooksPath 让钩子随仓库分发，验证 clone 后仍生效。
# 4. 思考：为什么“只靠本地钩子”不足以保证代码质量？
