# ===== 第094课：AI应用-大模型调用-HTTP请求数据格式 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - HTTP 请求体常见格式：application/json、表单、multipart/form-data
#   - 大模型 API 普遍使用 JSON：核心是字典和列表的嵌套
#   - json.dumps：Python 对象 -> JSON 字符串；json.loads：JSON 字符串 -> Python 对象
#   - 中文建议使用 ensure_ascii=False，避免被转义成 \uXXXX
#   - 请求头必须声明 Content-Type: application/json
#   - DeepSeek 请求体核心字段：model、messages、stream、temperature、max_tokens
#   - 响应核心字段：choices[0].message.content 与 usage 中的 token 统计
# 依赖：无（仅使用标准库 json；实际发送请求需 pip install requests）

import json


def build_payload(question):
    """构造一个符合 DeepSeek 对话接口要求的请求体。"""
    return {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个简洁的中文助手。"},
            {"role": "user", "content": question},
        ],
        "stream": False,        # 非流式，便于先理解请求/响应结构
        "temperature": 0.7,    # 控制回答的随机性
        "max_tokens": 512,     # 限制回答的最大长度
    }


def show_request(payload):
    """把请求体转成 JSON 字符串，并模拟请求头。"""
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    print("请求头：")
    print("  Content-Type: application/json")
    print("  Authorization: Bearer sk-你的密钥")  # 真实密钥不要写死在代码里
    print("请求体：")
    print(body)
    return body


if __name__ == "__main__":
    payload = build_payload("用一句话介绍 Python。")
    show_request(payload)

    # 下面的字符串模拟服务端返回的 JSON 响应，便于练习解析
    response_text = """
    {
      "choices": [
        {"message": {"role": "assistant", "content": "Python 是一门易学的编程语言。"}}
      ],
      "usage": {"prompt_tokens": 20, "completion_tokens": 12, "total_tokens": 32}
    }
    """
    data = json.loads(response_text)
    answer = data["choices"][0]["message"]["content"]
    usage = data["usage"]
    print("\n解析响应：")
    print(f"回答：{answer}")
    print(f"共使用 token：{usage['total_tokens']}")

# ===== 练习题 =====
# 1. 在 messages 中增加一条 assistant 历史消息，再增加一条新的 user 消息。
# 2. 解析响应并分别打印 prompt_tokens、completion_tokens、total_tokens。
# 3. 自测：json.dumps 和 json.loads 的区别是什么？为什么请求头要写 Content-Type？
