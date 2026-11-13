# ===== 第098课：AI应用-大模型调用-代码调用大模型 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 使用 OpenAI 官方 Python SDK 调用 DeepSeek，因为 DeepSeek 兼容 OpenAI 接口
#   - 安装依赖：pip install openai
#   - 创建客户端：OpenAI(api_key=密钥, base_url="https://api.deepseek.com")
#   - 调用对话：client.chat.completions.create(model=..., messages=...)
#   - 回答位置：response.choices[0].message.content
#   - 密钥从环境变量读取，代码中只保留占位符，避免泄露
#   - 网络调用要设置 timeout，并捕获认证失败、限流、连接异常等错误
# 依赖：pip install openai

import os
from openai import OpenAI

# 优先从环境变量读取；占位符仅用于展示，禁止提交真实密钥
API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-你的密钥")
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")


def chat_with_model(question):
    """向 DeepSeek 发送一次对话请求，返回回答文本。"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是一个简洁、准确的中文助手。"},
            {"role": "user", "content": question},
        ],
        temperature=0.7,
        max_tokens=512,
        timeout=30,  # 单次请求最多等待 30 秒
    )
    return response.choices[0].message.content


def safe_chat(question):
    """对常见异常做统一处理，避免程序直接崩溃。"""
    try:
        return chat_with_model(question)
    except Exception as exc:  # 实际项目可细分 AuthenticationError 等异常
        return f"调用失败：{type(exc).__name__} - {exc}"


if __name__ == "__main__":
    print(safe_chat("用一句话介绍 Python 适合做什么。"))

# ===== 练习题 =====
# 1. 配置环境变量 DEEPSEEK_API_KEY，运行本文件，确认能打印模型回答。
# 2. 在 messages 中加入上一轮的 assistant 回答，再追问一个问题，实现两轮对话。
# 3. 自测：使用 openai SDK 与直接 requests 发送 HTTP 请求，各自适合什么场景？
