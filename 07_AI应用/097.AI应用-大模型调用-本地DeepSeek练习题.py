# ===== 第097课：AI应用-大模型调用-本地DeepSeek =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 本地 DeepSeek 通过 Ollama 运行，不需要 API Key，数据不离开本机
#   - 常用模型名：deepseek-r1:7b、deepseek-r1:1.5b（先 ollama pull 下载）
#   - 对话接口：POST http://localhost:11434/api/chat
#   - 请求体：model、messages、stream、options（如 temperature）
#   - 响应：message.content 是回答，eval_count 是生成的 token 数
#   - 本地模型效果和速度取决于内存/显存，首次加载通常较慢
#   - 调用前必须确认 Ollama 服务正在运行，且模型已经下载
# 依赖：pip install requests

import requests

BASE_URL = "http://localhost:11434"
MODEL = "deepseek-r1:7b"  # 若硬件较弱，可换成 deepseek-r1:1.5b


def local_chat(messages, temperature=0.7):
    """调用本地 DeepSeek 模型，返回 (回答文本, 生成token数)。"""
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat", json=payload, timeout=180
        )
        response.raise_for_status()
        data = response.json()
        answer = data.get("message", {}).get("content", "")
        return answer, data.get("eval_count", 0)
    except requests.exceptions.ConnectionError:
        return "无法连接 Ollama，请先启动服务并确认端口 11434 可访问。", 0
    except requests.exceptions.Timeout:
        return "本地模型响应超时，可能是硬件性能不足或模型正在首次加载。", 0
    except requests.exceptions.HTTPError as exc:
        return f"请求失败，请确认模型已下载（ollama list）：{exc}", 0


if __name__ == "__main__":
    history = [
        {"role": "system", "content": "你是一个简洁的中文助手。"},
        {"role": "user", "content": "用一句话说明本地部署大模型的好处。"},
    ]
    reply, tokens = local_chat(history)
    print("模型回答：", reply)
    print("生成 token 数：", tokens)

# ===== 练习题 =====
# 1. 先执行 ollama pull deepseek-r1:1.5b，再把 MODEL 改为该模型并运行本文件。
# 2. 修改 messages，加入一轮 assistant 历史，观察模型是否能接着上下文回答。
# 3. 自测：本地 DeepSeek 为什么不需要 API Key？它和云端 DeepSeek 各自的优缺点是什么？
