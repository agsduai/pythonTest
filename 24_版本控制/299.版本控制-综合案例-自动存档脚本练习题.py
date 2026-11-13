# ===== 第299课：版本控制-综合案例-自动存档脚本 =====
# 知识点：
#   - 综合运用：subprocess 驱动 git + argparse（第276课）+ 干净的退出码
#   - 场景：auto_commit(repo, message, tag) 一行完成“暂存+提交+打标签”
#   - 无变更时优雅跳过，而不是报错

import argparse
import shutil
import stat
import subprocess
import sys
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



def git(*args, cwd, check=True):
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True,
        encoding="utf-8", errors="replace",
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 失败：\n{result.stderr}")
    return (result.stdout + result.stderr).strip()


def auto_commit(repo: Path, message: str, tag=None):
    """有变更就 add+commit（可选打 tag），没有变更就跳过。"""
    if not git("status", "--porcelain", cwd=repo):
        print("没有需要提交的变更，跳过")
        return False
    git("add", ".", cwd=repo)
    git("commit", "-m", message, cwd=repo)
    if tag:
        git("tag", tag, cwd=repo)
        print(f"已提交并打标签 {tag}：{message}")
    else:
        print(f"已提交：{message}")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description="自动存档：add + commit + 可选 tag")
    parser.add_argument("repo", help="仓库目录")
    parser.add_argument("-m", "--message", required=True, help="提交信息")
    parser.add_argument("--tag", help="可选标签名")
    args = parser.parse_args(argv)
    repo = Path(args.repo)
    if not (repo / ".git").exists():
        print(f"错误：{repo} 不是 git 仓库")
        return 2
    auto_commit(repo, args.message, args.tag)
    return 0


if __name__ == "__main__":
    # 内置演示：建临时仓库跑一遍
    DEMO = Path("git_demo_299")
    force_rmtree(DEMO)
    DEMO.mkdir()
    git("init", cwd=DEMO)
    git("config", "user.name", "学员", cwd=DEMO)
    git("config", "user.email", "student@example.com", cwd=DEMO)

    (DEMO / "app.py").write_text("v1\n", encoding="utf-8")
    main([str(DEMO), "-m", "第一版", "--tag", "v1.0"])
    (DEMO / "app.py").write_text("v2\n", encoding="utf-8")
    main([str(DEMO), "-m", "第二版"])
    main([str(DEMO), "-m", "没有变更的一次"])
    print("标签列表：", git("tag", cwd=DEMO))
    print("历史：", git("log", "--oneline", cwd=DEMO), sep="\n")
    force_rmtree(DEMO)

    # 真实使用：python 本文件.py 项目目录 -m "存档信息" --tag v2.0
    sys.exit(0)

# ===== 练习题 =====
# 1. 给 auto_commit 增加 --push 选项，提交后自动推送到 origin。
# 2. 结合第280课定时执行：每天 18 点自动 auto_commit 一次当日工作。
# 3. 思考：自动提交的 message 应该怎么写才有价值？
