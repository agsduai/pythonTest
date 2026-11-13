# ===== 第178课：Web应用-AI汉字谜盒-与AI交互(分析) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 对话消息格式：role 为 system/user/assistant，content 为文本
#   - 系统提示词约束 AI 的角色和回答风格
#   - 裁剪历史消息，避免上下文无限增长
#   - 使用 OpenAI 兼容 SDK 调用 DeepSeek 接口
# 依赖：pip install openai

import os

from openai import OpenAI

SYSTEM_PROMPT = (
    "你是“AI汉字谜盒”的猜字谜助手。"
    "每次先用一句谜面出题，不要直接公布谜底；"
    "用户回答后再判断对错，并给出简单解释。"
)

# 占位密钥：真实密钥请放在环境变量或 .env 中，严禁提交到代码仓库
API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-请替换为你的密钥")
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")


def build_messages(history: list[dict[str, str]], user_input: str) -> list[dict[str, str]]:
    """把系统提示词、最近历史和本轮输入组装成请求消息。"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history[-10:])  # 只保留最近 10 条，控制上下文长度
    messages.append({"role": "user", "content": user_input})
    return messages


def ask_ai(history: list[dict[str, str]], user_input: str) -> str:
    """调用大模型并返回文本回复。"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=build_messages(history, user_input),
        temperature=0.7,
    )
    usage = response.usage
    print(f"本次消耗 token：{usage.prompt_tokens} + {usage.completion_tokens}")
    return response.choices[0].message.content


if __name__ == "__main__":
    history: list[dict[str, str]] = []
    question = "给我出一个关于“明”字的谜语"
    answer = ask_ai(history, question)
    print("AI：", answer)

# ===== 练习题 =====
# 1. 说明 system、user、assistant 三种 role 分别在什么时候使用。
# 2. 为什么 build_messages 只取 history[-10:]，而不是带上全部历史？
# 3. 修改系统提示词，让 AI 出题后额外给一个字数提示。
