# ===== 第405课：Web API 与接口测试-最小 HTTP 服务与路由 =====
# 知识点：
#   - http.server：标准库自带的 HTTP 服务端，适合学习与内网小工具
#   - BaseHTTPRequestHandler：重写 do_GET/do_POST 等方法处理请求
#   - 路由表：{(方法, 路径): 处理函数}，把 URL 分发给业务函数
#   - 响应三件套：状态行、Content-Type、Content-Length，然后写 body
#   - 演示技巧：端口用 0 让系统分配；服务端跑在 daemon 线程；用完 shutdown
# 依赖：无（标准库 http.server / urllib.request）

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import urlopen

ROUTES = {}          # (method, path) -> handler


def route(method: str, path: str):
    """注册路由的装饰器。"""
    def decorator(func):
        ROUTES[(method, path)] = func
        return func
    return decorator


@route("GET", "/")
def index(req):
    return 200, {"message": "欢迎访问迷你 API", "routes": ["/hello", "/about"]}


@route("GET", "/hello")
def hello(req):
    name = req.query.get("name", ["世界"])[0]     # 查询参数是列表
    return 200, {"message": f"你好，{name}！"}


@route("GET", "/about")
def about(req):
    return 200, {"name": "mini-api", "version": "0.1.0", "framework": "http.server"}


class Handler(BaseHTTPRequestHandler):
    """把 HTTP 请求翻译成“路由查询 + 调用业务函数”。"""

    def _handle(self, method: str):
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(self.path)
        handler = ROUTES.get((method, parsed.path))
        if handler is None:
            status, payload = 404, {"error": f"未找到 {method} {parsed.path}"}
        else:
            self.query = parse_qs(parsed.query)
            try:
                status, payload = handler(self)
            except Exception as exc:              # 兜底：不让异常直接炸连接
                status, payload = 500, {"error": f"服务端错误：{exc}"}
        self._send_json(status, payload)

    def _send_json(self, status: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._handle("GET")

    def log_message(self, *args):
        pass                                       # 关闭默认访问日志


def start_server(handler_cls=Handler):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, server.server_address[1]


def main():
    server, thread, port = start_server()
    base = f"http://127.0.0.1:{port}"
    print(f"服务已启动：{base}")

    try:
        for path in ("/", "/hello?name=" + quote("小明"), "/about", "/not-exist"):
            try:
                with urlopen(base + path) as resp:
                    print(f"\nGET {path} → {resp.status}")
                    print(" ", json.loads(resp.read().decode("utf-8")))
            except HTTPError as exc:            # 404 等错误也按 JSON 返回
                print(f"\nGET {path} → {exc.code}")
                print(" ", json.loads(exc.read().decode("utf-8")))
    finally:
        server.shutdown()          # 停止 serve_forever
        server.server_close()
        thread.join(timeout=2)
        print("\n服务已关闭")


main()

# ===== 练习题 =====
# 1. 增加 GET /time 返回当前时间（第230课）。
# 2. 增加 GET /echo?msg=xxx 原样返回 msg。
# 3. 让 /hello 支持两个名字参数（?name=a&name=b）并全部返回。
# 4. 思考：为什么服务端代码必须捕获异常后再返回 500？
