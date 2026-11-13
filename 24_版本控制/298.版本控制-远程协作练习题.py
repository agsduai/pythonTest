# ===== 第298课：版本控制-远程协作 =====
# 知识点：
#   - 远程仓库：团队共享的“中央存档”（GitHub/Gitee/公司内网）
#   - 本课用“本地裸仓库”模拟远端 —— 协议流程与真实远端完全一致
#   - clone 拉取全量历史；push 上传；pull 下载并合并
#   - 典型循环：pull → 改 → commit → push

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


PARENT = Path("git_demo_298")
force_rmtree(PARENT)
PARENT.mkdir()
REMOTE = PARENT / "remote.git"          # 裸仓库：只有版本库，没有工作区
WORK = PARENT / "work"                  # 我的仓库
COLLEAGUE = PARENT / "colleague"        # 同事的仓库


def git(*args, cwd, check=True):
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True,
        encoding="utf-8", errors="replace",
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 失败：\n{result.stderr}")
    return (result.stdout + result.stderr).strip()


def setup_identity(repo):
    git("config", "user.name", "学员", cwd=repo)
    git("config", "user.email", "student@example.com", cwd=repo)


# ---- 1. “远端”与“我的仓库” ----
REMOTE_ABS = str(REMOTE.resolve())       # 统一用绝对路径，避免相对路径随 cwd 变化
git("init", "--bare", REMOTE_ABS, cwd=PARENT)
WORK.mkdir()                             # git init 不会自动创建目录
git("init", cwd=WORK)
setup_identity(WORK)
(WORK / "app.py").write_text("print('v1')\n", encoding="utf-8")
git("add", ".", cwd=WORK)
git("commit", "-m", "v1", cwd=WORK)
git("remote", "add", "origin", REMOTE_ABS, cwd=WORK)   # 必须用绝对路径：相对路径会相对当前工作目录解析
git("push", "-u", "origin", "HEAD", cwd=WORK)      # 首次推送并建立跟踪
print("已推送到远端")

# ---- 2. 同事克隆、开发、推送 ----
git("clone", REMOTE_ABS, "colleague", cwd=PARENT)
setup_identity(COLLEAGUE)
(COLLEAGUE / "feature.py").write_text("# 同事的新功能\n", encoding="utf-8")
git("add", ".", cwd=COLLEAGUE)
git("commit", "-m", "同事：新增 feature.py", cwd=COLLEAGUE)
git("push", cwd=COLLEAGUE)
print("同事已推送")

# ---- 3. 我拉取同事的成果 ----
print("pull 前本地文件：", sorted(p.name for p in WORK.iterdir() if p.is_file()))
print(git("pull", cwd=WORK))
print("pull 后本地文件：", sorted(p.name for p in WORK.iterdir() if p.is_file()))
print("完整历史：", git("log", "--oneline", cwd=WORK), sep="\n")

force_rmtree(PARENT)

# ===== 练习题 =====
# 1. 在 GitHub/Gitee 建一个真实远程仓库，把本项目 push 上去。
# 2. 制造“同事和我改同一行”的远程冲突：push 被拒后 pull 再解决。
# 3. 思考：push 被拒绝（non-fast-forward）通常是什么原因？
