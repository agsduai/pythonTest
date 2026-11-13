# ===== 第292课：版本控制-概念与首次配置 =====
# 知识点：
#   - 版本控制：给代码做“存档”，随时回退、对比、协作
#   - Git 三区模型：工作区 →(add)→ 暂存区 →(commit)→ 版本库
#   - 仓库身份：user.name / user.email，--local 只对当前仓库生效
#   - 本课所有操作都在临时目录里进行，不影响你的真实项目
#   - Python 侧技能：subprocess 调用外部命令（复习第233课）

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


DEMO = Path("git_demo_292")
force_rmtree(DEMO)
DEMO.mkdir()


def git(*args, cwd=DEMO, check=True):
    """运行 git 命令，返回输出文本；check=True 时失败即抛错。"""
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True,
        encoding="utf-8", errors="replace",
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 失败：\n{result.stderr}")
    return (result.stdout + result.stderr).strip()


# git 是否可用、什么版本
print("版本：", git("--version"))

# 初始化仓库：目录下多出 .git 隐藏目录，这里就是“版本库”
git("init")
print("已初始化：", (DEMO / ".git").exists())

# 配置本仓库的提交身份（不加 --global，不影响全局设置）
git("config", "user.name", "课程学员")
git("config", "user.email", "student@example.com")
print("身份：", git("config", "user.name"), "<", git("config", "user.email"), ">")

# 空仓库状态
print("状态输出（空仓库）：", repr(git("status", "--short")))

force_rmtree(DEMO)     # 清理演示目录

# ===== 练习题 =====
# 1. 查看你的全局 git 身份：git config --global user.name（没有就配置一次）。
# 2. 把 git init 后的 .git 目录列出来，看看里面有什么（只看不删）。
# 3. 思考：为什么 git commit 之前必须配置身份？
