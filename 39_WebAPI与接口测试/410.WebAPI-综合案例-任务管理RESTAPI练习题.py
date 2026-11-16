# ===== 第410课：Web API 与接口测试-综合案例-任务管理REST API =====
# 知识点：
#   - 综合运用：路由（405/407）+ 参数校验（406）+ 中间件（408）+ SQLite（407）
#   - 完整 API：健康检查、列表、创建、更新、删除，统一响应结构与状态码
#   - 鉴权：写操作需要 X-Token；读操作与健康检查开放
#   - 接口测试：启动真实服务（端口 0）→ 发真实 HTTP 请求 → 断言状态码与数据
#   - 测试与实现放在同一文件便于学习；真实项目应拆分 app.py / test_app.py
# 依赖：无（标准库）

import json
import re
import sqlite3
import tempfile
import threading
import unittest
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request as UrlRequest, urlopen

DB_PATH = ""
LOG: list[tuple] = []


@dataclass
class Request:
    method: str
    path: str
    headers: dict = field(default_factory=dict)
    body: dict = field(default_factory=dict)


@dataclass
class Response:
    status: int
    payload: dict | None = None


# ---------------- 数据库 ----------------
@contextmanager
def get_conn():
    """每请求独立连接；退出时提交并真正关闭（Windows 上否则会锁文件）。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                priority INTEGER NOT NULL DEFAULT 3,
                done INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.commit()


def row_to_dict(row):
    return {**dict(row), "done": bool(row["done"])}


# ---------------- 中间件 ----------------
def error_mw(req, nxt):
    try:
        return nxt(req)
    except Exception as exc:
        return Response(500, {"code": 500, "message": f"内部错误：{exc}"})


def logging_mw(req, nxt):
    resp = nxt(req)
    LOG.append((req.method, req.path, resp.status))
    return resp


def auth_mw(req, nxt):
    if req.method == "GET" or req.path == "/health":
        return nxt(req)
    if req.headers.get("X-Token") != "secret":
        return Response(401, {"code": 401, "message": "写操作需要 X-Token: secret"})
    return nxt(req)


# ---------------- 应用 ----------------
class App:

    def __init__(self):
        self.routes = []
        self.middlewares = []

    def route(self, method, pattern):
        def deco(func):
            self.routes.append((method, re.compile(f"^{pattern}$"), func))
            return func
        return deco

    def use(self, mw):
        self.middlewares.append(mw)
        return self

    def dispatch(self, req):
        endpoint = lambda r: Response(404, {"code": 404, "message": "未找到该接口"})
        for method, pattern, handler in self.routes:
            match = pattern.match(req.path)
            if method == req.method and match:
                endpoint = lambda r, h=handler, m=match: h(r, m)
                break
        chain = endpoint
        for mw in reversed(self.middlewares):
            nxt = chain
            chain = lambda r, mw=mw, nxt=nxt: mw(r, nxt)
        return chain(req)


app = App()
app.use(error_mw).use(logging_mw).use(auth_mw)


@app.route("GET", r"/health")
def health(req, match):
    return Response(200, {"code": 0, "data": "ok"})


@app.route("GET", r"/tasks")
def list_tasks(req, match):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()
    return Response(200, {"code": 0, "data": [row_to_dict(r) for r in rows]})


@app.route("POST", r"/tasks")
def create_task(req, match):
    title = str(req.body.get("title", "")).strip()
    priority = req.body.get("priority", 3)
    if not title:
        return Response(422, {"code": 422, "message": "title 不能为空"})
    if isinstance(priority, bool) or not isinstance(priority, int) or not (1 <= priority <= 5):
        return Response(422, {"code": 422, "message": "priority 必须是 1~5 的整数"})
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO tasks (title, priority) VALUES (?, ?)",
                           (title, priority))
        conn.commit()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
    return Response(201, {"code": 0, "data": row_to_dict(row)})


@app.route("PATCH", r"/tasks/(\d+)")
def patch_task(req, match):
    task_id = int(match.group(1))
    done = req.body.get("done")
    title = req.body.get("title")
    if done is not None and not isinstance(done, bool):
        return Response(422, {"code": 422, "message": "done 必须是布尔值"})
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            return Response(404, {"code": 404, "message": f"任务 {task_id} 不存在"})
        conn.execute(
            "UPDATE tasks SET title = COALESCE(?, title), done = COALESCE(?, done) WHERE id = ?",
            (title, None if done is None else int(done), task_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return Response(200, {"code": 0, "data": row_to_dict(row)})


@app.route("DELETE", r"/tasks/(\d+)")
def delete_task(req, match):
    task_id = int(match.group(1))
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        deleted = cur.rowcount
    if not deleted:
        return Response(404, {"code": 404, "message": f"任务 {task_id} 不存在"})
    return Response(204, None)


# ---------------- HTTP 适配 ----------------
class Handler(BaseHTTPRequestHandler):

    def _handle(self, method):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw.decode("utf-8")) if raw else {}
        except ValueError:
            self._send(400, {"code": 400, "message": "请求体不是合法 JSON"})
            return
        req = Request(method, self.path.split("?")[0], dict(self.headers), body)
        resp = app.dispatch(req)
        self._send(resp.status, resp.payload)

    def _send(self, status, payload):
        if status == 204:
            self.send_response(204)
            self.end_headers()
            return
        body = json.dumps(payload or {}, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self): self._handle("GET")
    def do_POST(self): self._handle("POST")
    def do_PATCH(self): self._handle("PATCH")
    def do_DELETE(self): self._handle("DELETE")
    def log_message(self, *args): pass


@contextmanager
def serve(db_file: Path):
    global DB_PATH
    DB_PATH = str(db_file)
    init_db()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def call(base, method, path, payload=None, token="secret"):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Token"] = token
    req = UrlRequest(base + path, data=data, method=method, headers=headers)
    try:
        with urlopen(req) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw.decode("utf-8")) if raw else None)
    except HTTPError as exc:
        raw = exc.read()
        return exc.code, (json.loads(raw.decode("utf-8")) if raw else None)


# ---------------- 接口测试 ----------------
class TestTaskAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.ctx = serve(Path(cls.tmp.name) / "test.db")
        cls.base = cls.ctx.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.ctx.__exit__(None, None, None)
        cls.tmp.cleanup()

    def test_health(self):
        status, body = call(self.base, "GET", "/health", token=None)
        self.assertEqual(status, 200)
        self.assertEqual(body["data"], "ok")

    def test_create_and_list(self):
        status, body = call(self.base, "POST", "/tasks", {"title": "测试任务", "priority": 2})
        self.assertEqual(status, 201)
        self.assertFalse(body["data"]["done"])
        status, body = call(self.base, "GET", "/tasks", token=None)
        self.assertEqual(status, 200)
        self.assertTrue(any(t["title"] == "测试任务" for t in body["data"]))

    def test_validation(self):
        status, body = call(self.base, "POST", "/tasks", {"title": "", "priority": 9})
        self.assertEqual(status, 422)
        self.assertIn("message", body)

    def test_auth_required_for_write(self):
        status, body = call(self.base, "POST", "/tasks", {"title": "hack"}, token=None)
        self.assertEqual(status, 401)

    def test_patch_and_delete(self):
        _, created = call(self.base, "POST", "/tasks", {"title": "待办"})
        task_id = created["data"]["id"]
        status, body = call(self.base, "PATCH", f"/tasks/{task_id}", {"done": True})
        self.assertEqual(status, 200)
        self.assertTrue(body["data"]["done"])
        status, _ = call(self.base, "DELETE", f"/tasks/{task_id}")
        self.assertEqual(status, 204)
        status, _ = call(self.base, "PATCH", f"/tasks/{task_id}", {"done": False})
        self.assertEqual(status, 404)


def demo():
    with tempfile.TemporaryDirectory() as tmp:
        with serve(Path(tmp) / "demo.db") as base:
            print("健康检查：", call(base, "GET", "/health", token=None))
            print("创建任务：", call(base, "POST", "/tasks", {"title": "写毕业项目"}))
            print("未带 token 写：", call(base, "POST", "/tasks", {"title": "x"}, token=None))
            print("任务列表：", call(base, "GET", "/tasks", token=None))
            print("访问日志：", LOG)


if __name__ == "__main__":
    demo()
    print("\n===== 运行接口测试 =====")
    unittest.main(exit=False, verbosity=2)

# ===== 练习题 =====
# 1. 增加 GET /tasks/{id} 详情接口，并补一个 404 测试。
# 2. 增加 ?done=1 过滤与分页参数（?page=1&size=10）。
# 3. 把鉴权 token 改成从环境变量读取（第402课），并补测试。
# 4. 思考：接口测试与单元测试（第34章）分别覆盖什么风险？
