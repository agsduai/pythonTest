# ===== 第093课：AI应用-大模型调用-HTTP协议介绍 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - HTTP 是“请求—响应”式应用层协议，浏览器和 Python 程序都用它访问 API
#   - 请求报文 = 请求行 + 请求头 + 空行 + 请求体
#       POST /chat/completions HTTP/1.1
#       Host: api.deepseek.com
#       Content-Type: application/json
#   - 响应报文 = 状态行 + 响应头 + 空行 + 响应体
#   - 常见方法：GET 查询、POST 提交、PUT 更新、DELETE 删除
#   - 常见状态码：200 成功、400 参数错误、401 未授权、404 路径错误、
#                 429 请求过多、500 服务器内部错误
#   - HTTPS 是在 HTTP 之下增加 TLS 加密，默认端口 443
# 依赖：无（仅使用标准库）

# 常见 HTTP 状态码及含义
STATUS_CODES = {
    200: "请求成功",
    400: "请求参数格式错误",
    401: "未提供或提供了无效的 API Key",
    403: "没有访问权限",
    404: "接口路径不存在",
    429: "请求过于频繁，被限流",
    500: "服务器内部错误",
}


def build_http_request(method, path, host, headers=None, body=None):
    """手工拼接一个 HTTP/1.1 请求报文，帮助理解请求结构。"""
    lines = [f"{method} {path} HTTP/1.1", f"Host: {host}"]
    headers = headers or {}
    if body is not None:
        # 请求体是 UTF-8 文本时，Content-Length 按字节数计算
        headers.setdefault("Content-Length", str(len(body.encode("utf-8"))))
    for key, value in headers.items():
        lines.append(f"{key}: {value}")
    lines.append("")          # 空行分隔请求头和请求体
    if body is not None:
        lines.append(body)
    return "\r\n".join(lines)


if __name__ == "__main__":
    request = build_http_request(
        method="POST",
        path="/chat/completions",
        host="api.deepseek.com",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer sk-你的密钥",  # 真实密钥不要硬编码
        },
        body='{"model": "deepseek-chat", "messages": []}',
    )
    print(request)
    print("\n状态码说明：")
    for code, meaning in STATUS_CODES.items():
        print(f"  {code}: {meaning}")

# ===== 练习题 =====
# 1. 用 build_http_request 构造一个访问本地 Ollama 的 GET 请求：
#    GET /api/tags，Host 为 localhost:11434。
# 2. 自测：分别说出 401、404、429 对应的常见原因和处理办法。
# 3. 思考：为什么调用大模型 API 通常用 POST，而不是 GET？
