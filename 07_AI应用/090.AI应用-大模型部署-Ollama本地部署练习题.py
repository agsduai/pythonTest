# ===== 第090课：AI应用-大模型部署-Ollama本地部署 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - Ollama 是本地运行开源大模型的工具，支持 Windows / macOS / Linux
#   - 安装：从官网 ollama.com 下载安装包，安装后在终端验证 ollama --version
#   - 常用命令：ollama pull deepseek-r1:7b 下载模型
#               ollama run deepseek-r1:7b 在终端对话
#               ollama list 查看已下载模型
#   - 安装后服务默认监听 http://localhost:11434；未启动时可在终端执行 ollama serve
#   - HTTP 接口：GET /api/tags 查看模型；POST /api/chat 进行对话
#   - 7B 模型通常建议至少 8GB 内存，1.5B 小模型对硬件要求更低
# 依赖：pip install requests

import requests

BASE_URL = "http://localhost:11434"  # Ollama 默认本地服务地址
MODEL = "deepseek-r1:7b"             # 需先执行 ollama pull deepseek-r1:7b


def list_models():
    """自检脚本：访问 /api/tags，确认 Ollama 服务是否可用。"""
    try:
        response = requests.get(f"{BASE_URL}/api/tags", timeout=3)
        response.raise_for_status()  # 状态码不是 2xx 时抛出异常
        models = response.json().get("models", [])
        if not models:
            print("服务可访问，但还没有下载模型，请执行：ollama pull deepseek-r1:7b")
            return
        print("Ollama 服务正常，已安装模型：")
        for item in models:
            print(f"  - {item.get('name')}")
    except requests.exceptions.ConnectionError:
        print("无法连接 Ollama：请先启动 Ollama，再重新运行本脚本。")
    except requests.exceptions.Timeout:
        print("连接超时：请检查 Ollama 是否正在运行。")
    except requests.exceptions.HTTPError as exc:
        print(f"服务返回异常状态码：{exc}")


def chat_once(prompt):
    """通过 /api/chat 调用本地模型（需先下载模型并启动服务）。"""
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,  # False 表示一次性返回完整结果
    }
    response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    return data["message"]["content"]


if __name__ == "__main__":
    list_models()
    # 确认服务与模型都可用后，可取消下面两行注释体验本地对话：
    # answer = chat_once("用一句话介绍你自己")
    # print(answer)

# ===== 练习题 =====
# 1. 安装 Ollama 后，在终端执行 ollama --version 和 ollama list，记录版本与模型列表。
# 2. 运行本文件的 list_models()，确认 http://localhost:11434 是否可访问。
# 3. 自测：为什么 7B 模型通常比 1.5B 模型需要更多内存？下载前应确认什么？
