# ===== 第095课：AI应用-大模型调用-Apifox接口测试 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - Apifox 是常用的接口设计、调试与测试工具，可在不发代码的情况下验证 API
#   - 新建 HTTP 请求的步骤：选方法 -> 填 URL -> 配 Headers -> 写 Body -> 发送
#   - 测试 DeepSeek：POST https://api.deepseek.com/chat/completions
#   - Headers：Authorization: Bearer <密钥>；Content-Type: application/json
#   - Body 选择 JSON，填入 model 与 messages 字段
#   - 可把 base_url、api_key 配成环境变量，在请求中引用，避免反复修改
#   - 常见结果：200 成功、400 请求体格式错误、401 密钥错误、429 触发限流
# 依赖：无（仅使用标准库 json；接口测试在 Apifox 中完成）

import json

API_URL = "https://api.deepseek.com/chat/completions"


def build_body(question):
    """生成 Apifox 的 Body -> JSON 内容。"""
    return {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": question}],
        "stream": False,
    }


def check_request(api_key, body):
    """发送前自检：检查密钥占位符、URL、JSON 是否合法。"""
    problems = []
    if not api_key or api_key == "sk-你的密钥":
        problems.append("API Key 仍是占位符，请换成真实密钥（不要写进代码仓库）")
    if not API_URL.startswith("https://"):
        problems.append("URL 应以 https:// 开头")
    try:
        text = json.dumps(body, ensure_ascii=False)
        json.loads(text)  # 反向解析一次，确认 JSON 合法
    except (TypeError, ValueError) as exc:
        problems.append(f"请求体不是合法 JSON：{exc}")
    if "model" not in body or "messages" not in body:
        problems.append("请求体缺少 model 或 messages 字段")
    return problems


if __name__ == "__main__":
    payload = build_body("你好，请自我介绍一下。")
    print("Apifox 请求配置：")
    print(f"  方法：POST\n  URL：{API_URL}")
    print("  Header：Authorization = Bearer sk-你的密钥")
    print("  Header：Content-Type = application/json")
    print("  Body：")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("\n发送前自检：")
    issues = check_request("sk-你的密钥", payload)
    if issues:
        for item in issues:
            print(f"  - {item}")
    else:
        print("  配置看起来没问题，可以点击 Send 发送。")

# ===== 练习题 =====
# 1. 在 Apifox 中新建 POST 请求，按上面的配置调用 DeepSeek，记录状态码和响应内容。
# 2. 把 URL 和 API Key 配成环境变量，在请求中引用，并保存一个成功示例。
# 3. 自测：分别构造错误密钥、错误路径各请求一次，说明 401 与 404 的含义。
