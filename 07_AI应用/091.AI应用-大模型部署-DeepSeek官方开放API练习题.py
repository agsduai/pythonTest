# ===== 第091课：AI应用-大模型部署-DeepSeek官方开放API =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - DeepSeek 开放平台：platform.deepseek.com，注册后可创建 API Key
#   - API Key 只显示一次，应保存在环境变量中，绝不能提交到代码仓库
#   - DeepSeek API 兼容 OpenAI 格式，基础地址为 https://api.deepseek.com
#   - 对话接口：POST /chat/completions
#   - 常用模型：deepseek-chat（通用对话）、deepseek-reasoner（推理模型）
#   - 计费按输入/输出 token 计算，调用前应关注账户余额与限流说明
# 依赖：pip install requests

import os
import requests

# 从环境变量读取密钥；这里的占位符仅用于演示，不要提交真实密钥
API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-你的密钥")
BASE_URL = "https://api.deepseek.com"


def ask_deepseek(question, model="deepseek-chat"):
    """调用 DeepSeek 对话接口并返回回答文本。"""
    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",  # Bearer 后跟一个空格和密钥
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是一个乐于助人的中文助手。"},
            {"role": "user", "content": question},
        ],
        "stream": False,       # 关闭流式输出，一次性拿到完整结果
        "temperature": 0.7,   # 0 更稳定，数值越大越发散
    }
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    if response.status_code == 401:
        raise RuntimeError("API Key 无效，请检查环境变量 DEEPSEEK_API_KEY")
    if response.status_code == 402:
        raise RuntimeError("账户余额不足，请到开放平台充值")
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


if __name__ == "__main__":
    # 未配置密钥时会得到 401；这是正常的占位符保护，不影响阅读代码
    print(ask_deepseek("用一句话说明什么是大语言模型。"))

# ===== 练习题 =====
# 1. 到 DeepSeek 开放平台创建 API Key，并用 set 命令写入环境变量（不要写进代码）。
# 2. 把 ask_deepseek 的 model 改为 deepseek-reasoner，观察返回结构有什么不同。
# 3. 自测：为什么 API Key 不能直接写在 .py 文件里？应该怎样管理？
