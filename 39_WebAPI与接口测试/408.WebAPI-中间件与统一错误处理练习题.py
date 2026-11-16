# ===== 第408课：Web API 与接口测试-中间件与统一错误处理 =====
# 知识点：
#   - 中间件：在“请求进入业务”与“响应返回客户端”之间插入通用逻辑
#   - 典型中间件：错误兜底、访问日志、鉴权、限流、CORS
#   - 洋葱模型：先注册的中间件在最外层（先进入、最后返回）
#   - 统一错误处理：业务只抛异常，中间件负责翻译成标准 JSON + 状态码
#   - 与第191课生成器管道、第260课观察者一样，都是“横切关注点”的解法
# 依赖：无（标准库）

import json
import re
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request as UrlRequest, urlopen


@dataclass
class Request:
    method: str
    path: str
    query: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)
    body: dict = field(default_factory=dict)


@dataclass
class Response:
    status: int
    payload: dict | None = None
    headers: dict = field(default_factory=dict)


LOG: list[tuple] = []


# ---------------- 中间件 ----------------
def error_middleware(req: Request, nxt) -> Response:
    """最外层：任何未捕获异常都变成 500 JSON。"""
    try:
        return nxt(req)
    except Exception as exc:
        return Response(500, {"code": 500, "message": f"内部错误：{type(exc).__name__}: {exc}"})


def logging_middleware(req: Request, nxt) -> Response:
    start = time.perf_counter()
    resp = nxt(req)
    cost = (time.perf_counter() - start) * 1000
    LOG.append((req.method, req.path, resp.status, f"{cost:.1f}ms"))
    return resp


def auth_middleware(req: Request, nxt) -> Response:
    """/health 放行；其余要求 X-Token: secret。"""
    if req.path == "/health":
        return nxt(req)
    if req.headers.get("X-Token") != "secret":
        return Response(401, {"code": 401, "message": "缺少或错误的 X-Token"})
    return nxt(req)


# ---------------- 迷你应用 ----------------
class App:

    def __init__(self):
        self.routes: list[tuple[str, re.Pattern, callable]] = []
        self.middlewares: list[callable] = []

    def route(self, method: str, pattern: str):
        def decorator(func):
            self.routes.append((method, re.compile(f"^{pattern}$"), func))
            return func
        return decorator

    def use(self, middleware):
        self.middlewares.append(middleware)
        return self

    def dispatch(self, req: Request) -> Response:
        endpoint = self._find_endpoint(req)
        chain = endpoint
        for mw in reversed(self.middlewares):          # 先注册的在最外层
            nxt = chain
            chain = lambda r, mw=mw, nxt=nxt: mw(r, nxt)
        return chain(req)

    def _find_endpoint(self, req: Request):
        for method, pattern, handler in self.routes:
            if method != req.method:
                continue
            match = pattern.match(req.path)
            if match:
                return lambda r, h=handler, m=match: h(r, m)
        return lambda r: Response(404, {"code": 404, "message": f"未找到 {r.method} {r.path}"})


app = App()
app.use(error_middleware).use(logging_middleware).use(auth_middleware)


@app.route("GET", r"/health")
def health(req, match):
    return Response(200, {"code": 0, "data": "ok"})


@app.route("GET", r"/profile")
def profile(req, match):
    return Response(200, {"code": 0, "data": {"user": "小明", "role": "admin"}})


@app.route("GET", r"/boom")
def boom(req, match):
    raise RuntimeError("数据库连接池耗尽")       # 故意抛异常，看中间件兜底


# ---------------- HTTP 适配层 ----------------
class Handler(BaseHTTPRequestHandler):

    def _handle(self, method):
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw.decode("utf-8")) if raw else {}
        except ValueError:
            body = {}
        req = Request(method, parsed.path, parse_qs(parsed.query), dict(self.headers), body)
        resp = app.dispatch(req)
        payload = resp.payload if resp.payload is not None else {}
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(resp.status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        for k, v in resp.headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self): self._handle("GET")
    def do_POST(self): self._handle("POST")
    def log_message(self, *args): pass


def call(base, path, token=None):
    headers = {"X-Token": token} if token else {}
    try:
        with urlopen(UrlRequest(base + path, headers=headers)) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
base = f"http://127.0.0.1:{server.server_address[1]}"

try:
    print("健康检查（免鉴权）：", call(base, "/health"))
    print("无 token 访问：", call(base, "/profile"))
    print("带 token 访问：", call(base, "/profile", token="secret"))
    print("触发异常（被兜底）：", call(base, "/boom", token="secret"))
    print("未知路由：", call(base, "/nope", token="secret"))
    print("\n访问日志：")
    for entry in LOG:
        print("  ", entry)
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)

# ===== 练习题 =====
# 1. 增加限流中间件：同一路径 1 秒内超过 5 次返回 429。
# 2. 增加 CORS 中间件：所有响应带 Access-Control-Allow-Origin: *。
# 3. 让错误中间件区分 ValueError（400）与其他异常（500）。
# 4. 思考：中间件顺序换一下（auth 在 error 外层），行为会怎样变？
