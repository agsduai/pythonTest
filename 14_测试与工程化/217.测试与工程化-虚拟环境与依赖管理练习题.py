# ===== 第217课：测试与工程化-虚拟环境与依赖管理 =====
# 知识点：
#   - 虚拟环境：每个项目独立的包环境，避免版本冲突
#   - 创建：python -m venv .venv；激活后 pip install 装进项目内
#   - 依赖清单：pip freeze > requirements.txt；还原：pip install -r requirements.txt
#   - 团队协作：代码进 git，.venv 不进 git（本项目的 .gitignore 已排除）
#   - sys.executable / sys.prefix 可确认当前用的是哪个环境

import importlib.util
import sys

print("当前解释器：", sys.executable)
print("环境位置　：", sys.prefix)
print("Python版本：", sys.version.split()[0])

# 常用命令速查（在终端执行）：
#   python -m venv .venv                 # 创建虚拟环境
#   .venv\Scripts\activate               # Windows 激活
#   source .venv/bin/activate            # macOS/Linux 激活
#   deactivate                           # 退出虚拟环境
#   pip install requests                 # 安装包
#   pip list                             # 查看已装包
#   pip freeze > requirements.txt        # 导出依赖清单
#   pip install -r requirements.txt      # 按清单还原
#   pip install pytest -i https://pypi.tuna.tsinghua.edu.cn/simple  # 国内镜像加速


# 检查当前环境是否装了某个包
def has_package(name):
    return importlib.util.find_spec(name) is not None


print("openai 已安装：", has_package("openai"))
print("pytest 已安装：", has_package("pytest"))
print("pandas 已安装：", has_package("pandas"))

# ===== 练习题 =====
# 1. 在终端执行 pip list，记录本机已装的包。
# 2. 导出 requirements.txt，再新建一个虚拟环境用清单还原依赖。
# 3. 用 has_package 检查第 098 课需要的 openai 是否已安装。
# 4. 思考：为什么不能把 .venv 文件夹提交到 git？
