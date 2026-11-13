# ===== 第295课：版本控制-撤销与回退 =====
# 知识点：
#   - 改错了还没 add：git restore <文件> 丢弃工作区修改
#   - add 错了：git restore --staged <文件> 撤回暂存（文件内容保留）
#   - 提交错了：git reset --soft HEAD~1 撤销提交，改动回到暂存区
#   - git reset --hard HEAD~1 撤销提交+丢弃改动（危险，慎用）
#   - 越靠后的撤销“破坏力”越大，先想清楚再执行

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


DEMO = Path("git_demo_295")
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
(DEMO / "app.py").write_text("print('v1')\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "v1")

# ---- 场景1：改错了，还没 add → restore 丢弃 ----
(DEMO / "app.py").write_text("print('写错了')\n", encoding="utf-8")
git("restore", "app.py")
print("场景1 还原后内容：", (DEMO / "app.py").read_text(encoding="utf-8").strip())

# ---- 场景2：add 错了 → 撤回暂存 ----
(DEMO / "app.py").write_text("print('v2')\n", encoding="utf-8")
git("add", ".")
git("restore", "--staged", "app.py")
print("场景2 撤回暂存后：", git("status", "--short"), "（M 在右侧=未暂存）")

# ---- 场景3：提交错了 → reset --soft（改动保留在暂存区）----
git("add", ".")
git("commit", "-m", "v2 写错了提交信息")
git("reset", "--soft", "HEAD~1")
print("场景3 soft 回退后：", git("status", "--short"), "改动还在暂存区")
git("commit", "-m", "v2（正确的提交信息）")

# ---- 场景4：reset --hard（连改动一起丢，演示用）----
git("reset", "--hard", "HEAD~1")
print("场景4 hard 回退后文件：", (DEMO / "app.py").read_text(encoding="utf-8").strip())
print("最终历史：", git("log", "--oneline"))

force_rmtree(DEMO)

# ===== 练习题 =====
# 1. 把场景3改成 reset --mixed（默认），观察与 --soft 的区别。
# 2. 思考：为什么团队规范都警告 --hard？什么时候它才是正确选择？
# 3. 进阶：commit 已经 push 到远端后，还能用 reset 撤吗？该用什么？（revert）
