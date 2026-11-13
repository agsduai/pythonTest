# ===== 第103课：AI应用-实战-准备工作(AI插件安装) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 实战前准备：安装 PyCharm AI 编程插件，并统一项目运行环境
#   - 安装路径：PyCharm 中打开 Settings（Ctrl+Alt+S）-> Plugins -> Marketplace
#   - 搜索并安装 AI 助手插件（如通义灵码、CodeGeeX、GitHub Copilot），完成后重启
#   - 在插件面板登录账号，即可使用代码补全、对话问答、解释代码等功能
#   - 安全提醒：AI 生成的代码要人工检查；不要把 API Key、密码等隐私粘贴给插件
#   - 后续项目依赖：streamlit（界面）、openai（调用模型）、requests（HTTP 请求）
#   - 建议使用虚拟环境，并把依赖写入 requirements.txt 方便复现
# 依赖：无（本课为环境准备，仅使用标准库检查环境）

import importlib.util
import os
import sys

REQUIRED_PACKAGES = {
    "streamlit": "搭建网页界面",
    "openai": "使用 OpenAI 兼容 SDK 调用大模型",
    "requests": "发送 HTTP 请求",
}


def check_python():
    """检查 Python 版本是否满足后续课程需要。"""
    version = sys.version.split()[0]
    print(f"Python 版本：{version}")
    if sys.version_info < (3, 10):
        print("  建议升级到 Python 3.10 及以上版本")


def check_packages():
    """检查后续实战需要的第三方库是否已经安装。"""
    print("\n依赖检查：")
    missing = []
    for name, purpose in REQUIRED_PACKAGES.items():
        installed = importlib.util.find_spec(name) is not None
        print(f"  {name:<10}{'已安装' if installed else '未安装'}（{purpose}）")
        if not installed:
            missing.append(name)
    if missing:
        print("  安装命令：pip install " + " ".join(missing))
    return missing


def check_api_key():
    """检查 DeepSeek 密钥是否已放入环境变量，只显示末 4 位。"""
    key = os.getenv("DEEPSEEK_API_KEY", "")
    if not key or key == "sk-你的密钥":
        print("\n未检测到 DEEPSEEK_API_KEY，请先在环境变量中配置（不要写进代码）。")
    else:
        print(f"\n已检测到 DEEPSEEK_API_KEY，末 4 位：{key[-4:]}")


if __name__ == "__main__":
    print("== 第103课 环境自检 ==")
    check_python()
    check_packages()
    check_api_key()
    print("\n插件安装为手工步骤：Settings -> Plugins -> Marketplace -> 搜索 AI 插件。")

# ===== 练习题 =====
# 1. 在 PyCharm 中安装一个 AI 编程插件并登录，试用“解释选中代码”功能。
# 2. 运行本文件完成环境自检，根据提示安装缺少的库。
# 3. 自测：为什么不能把 API Key 或公司代码直接粘贴到 AI 插件对话中？
