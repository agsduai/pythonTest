# ===== 第173课：Web应用-FastAPI基础-Web初识 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - Web 的本质：浏览器（客户端）与服务器通过 HTTP 协议通信
#   - URL 的组成：协议、主机、端口、路径、查询参数
#   - 常见请求方法：GET 用于查询，POST 用于提交数据
#   - 常见状态码：200 成功、404 未找到、500 服务器错误
#   - 响应体常见格式：HTML、JSON
# 依赖：无（示例使用 Python 标准库 http.server）

from http.server import BaseHTTPRequestHandler, HTTPServer
import json


class DemoHandler(BaseHTTPRequestHandler):
    """最小 Web 服务器：演示请求与响应的处理过程。"""

    def do_GET(self):
        # self.path 是请求路径，例如 /hello?name=小明
        if self.path.startswith("/hello"):
            # 构造 JSON 响应体，并显式使用 UTF-8 编码
            body = json.dumps({"message": "你好，Web！"}, ensure_ascii=False).encode("utf-8")
            self.send_response(200)  # 状态码 200 表示请求成功
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            # 路径不存在时返回 404
            self.send_error(404, "Not Found")

    def do_POST(self):
        # 先读请求体长度，再读取请求体数据
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8")
        body = json.dumps({"received": raw}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    # 127.0.0.1 表示本机；8000 是端口号
    server = HTTPServer(("127.0.0.1", 8000), DemoHandler)
    print("服务已启动：http://127.0.0.1:8000/hello")
    server.serve_forever()

# ===== 练习题 =====
# 1. 画图说明浏览器访问 http://127.0.0.1:8000/hello?name=小明 的完整过程。
# 2. 修改示例，让 /hello 读取查询参数 name，并返回“你好，name！”。
# 3. 新增 /time 接口，返回服务器当前时间（JSON 格式）。
