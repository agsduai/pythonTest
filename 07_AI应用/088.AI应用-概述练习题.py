# ===== 第088课：AI应用-概述 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - AI 应用 = 大模型能力 + Python 程序 + 用户界面
#   - 大模型常见能力：对话问答、文本总结、翻译、写作、代码生成
#   - 使用大模型的两条路线：调用官方 API（云端）与本地部署（Ollama）
#   - 本课程技术栈：Python + DeepSeek / Ollama + Streamlit
#   - 典型应用：智能客服、写作助手、知识库问答、AI 编程助手
# 依赖：无（本课为概念课，仅使用标准库）

import importlib.util
import sys


def check_environment():
    """环境自检：确认 Python 版本与后续课程要用的第三方库。"""
    print(f"Python 版本：{sys.version.split()[0]}")
    if sys.version_info < (3, 10):
        print("提示：建议使用 Python 3.10 及以上版本")

    # find_spec 只检查模块是否可找到，不会真正导入模块
    for name in ["requests", "openai", "streamlit"]:
        installed = importlib.util.find_spec(name) is not None
        status = "已安装" if installed else "未安装"
        print(f"{name:<12}{status}")


def describe_ai_app():
    """用字典描述一个 AI 应用的基本组成。"""
    app = {
        "名称": "课程问答助手",
        "输入": "用户用自然语言提出的问题",
        "大模型": "DeepSeek（负责理解问题与生成回答）",
        "程序": "Python（负责组装请求、保存会话）",
        "界面": "Streamlit（负责网页交互）",
    }
    for key, value in app.items():
        print(f"{key}：{value}")


if __name__ == "__main__":
    check_environment()
    print("-" * 40)
    describe_ai_app()
    print("-" * 40)
    print("AI 应用的本质：把大模型能力封装成普通用户可用的产品。")

# ===== 练习题 =====
# 1. 写出你日常使用过的 3 个 AI 应用，并说明它们分别用到了大模型的哪些能力。
# 2. 运行示例代码，记录你的环境中 requests、openai、streamlit 的安装情况。
# 3. 用自己的话说明“调用云端 API”和“本地部署大模型”的区别与适用场景。
