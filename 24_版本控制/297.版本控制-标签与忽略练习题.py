# ===== 第297课：版本控制-标签与忽略 =====
# 知识点：
#   - tag：给某个提交起“版本号”名字，发布版本的标准做法
#   - 附注标签 -a -m：带说明和作者的正式标签
#   - .gitignore：声明不入库的文件（日志、缓存、依赖、临时产物）
#   - 本项目的 .gitignore 就排除了 .venv / .idea / __pycache__

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


DEMO = Path("git_demo_297")
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

# ---- 标签 ----
git("tag", "v1.0")                       # 轻量标签：只是个名字
git("tag", "-a", "v1.0-final", "-m", "首个正式版本")   # 附注标签
print("所有标签：", git("tag"))
print("附注标签信息：", git("show", "v1.0-final", "--stat"), sep="\n")

# ---- .gitignore ----
(DEMO / ".gitignore").write_text("*.log\nbuild/\n__pycache__/\n", encoding="utf-8")
(DEMO / "debug.log").write_text("日志", encoding="utf-8")
(DEMO / "build").mkdir()
(DEMO / "build" / "app.exe").write_text("产物", encoding="utf-8")

print("状态（只显示 .gitignore，其余被忽略）：", git("status", "--short"))
git("add", ".")
git("commit", "-m", "添加忽略规则")
print("入库文件：", git("ls-files"))

# 已入库的文件 .gitignore 管不了（要先 git rm --cached 移出）
print("验证：debug.log 在不在版本库：", "debug.log" in git("ls-files"))

force_rmtree(DEMO)

# ===== 练习题 =====
# 1. 查看本项目 pyproject01 的 .gitignore 内容，逐条说明它在忽略什么。
# 2. 模拟“log 文件已被提交”的情况，用 git rm --cached 移出并验证。
# 3. 思考：.venv、.idea、__pycache__ 为什么都不该入库？
