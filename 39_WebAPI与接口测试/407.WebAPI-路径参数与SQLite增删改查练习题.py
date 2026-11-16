# ===== 第407课：Web API 与接口测试-路径参数与SQLite增删改查 =====
# 知识点：
#   - 路径参数：/tasks/1 用正则 (\d+) 捕获，路由从“精确匹配”升级为“模式匹配”
#   - CRUD 对应：POST 创建 / GET 列表与详情 / PUT 更新 / DELETE 删除
#   - 参数化 SQL（第207课）+ 每请求独立连接（线程安全）
#   - 404 判定：更新/删除/查询前先确认存在
#   - 数据库用临时文件（:memory: 不能跨连接共享）
# 依赖：无（sqlite3 内置）

import json
import re
import sqlite3
import tempfile
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

DB_PATH = None            # 由 main 设置
ROUTES = []               # (method, compiled_pattern, handler)


def route(method, pattern):
    def decorator(func):
        ROUTES.append((method, re.compile(f"^{pattern}$"), func))
        return func
    return decorator


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


def rows_to_list(rows):
    return [dict(r) for r in rows]


# ---------------- 业务处理 ----------------
@route("GET", r"/tasks")
def list_tasks(match, body):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()
    return 200, {"code": 0, "data": rows_to_list(rows)}


@route("POST", r"/tasks")
def create_task(match, body):
    title = (body or {}).get("title", "").strip()
    priority = (body or {}).get("priority", 3)
    if not title:
        return 422, {"code": 422, "message": "title 不能为空"}
    if not isinstance(priority, int) or not (1 <= priority <= 5):
        return 422, {"code": 422, "message": "priority 必须是 1~5 的整数"}
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, priority) VALUES (?, ?)", (title, priority)
        )
        conn.commit()
        task_id = cur.lastrowid
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return 201, {"code": 0, "data": dict(row)}


@route("GET", r"/tasks/(\d+)")
def get_task(match, body):
    task_id = int(match.group(1))
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        return 404, {"code": 404, "message": f"任务 {task_id} 不存在"}
    return 200, {"code": 0, "data": dict(row)}


@route("PUT", r"/tasks/(\d+)")
def update_task(match, body):
    task_id = int(match.group(1))
    title = (body or {}).get("title")
    done = (body or {}).get("done")
    if title is not None and not str(title).strip():
        return 422, {"code": 422, "message": "title 不能为空"}
    if done is not None and not isinstance(done, bool):
        return 422, {"code": 422, "message": "done 必须是布尔值"}
    with get_conn() as conn:
        exists = conn.execute("SELECT 1 FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not exists:
            return 404, {"code": 404, "message": f"任务 {task_id} 不存在"}
        conn.execute(
            "UPDATE tasks SET title = COALESCE(?, title), done = COALESCE(?, done) "
            "WHERE id = ?",
            (title, done, task_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return 200, {"code": 0, "data": dict(row)}


@route("DELETE", r"/tasks/(\d+)")
def delete_task(match, body):
    task_id = int(match.group(1))
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        deleted = cur.rowcount
    if deleted == 0:
        return 404, {"code": 404, "message": f"任务 {task_id} 不存在"}
    return 204, None


class Handler(BaseHTTPRequestHandler):

    def _dispatch(self, method):
        for route_method, pattern, handler in ROUTES:
            if route_method != method:
                continue
            match = pattern.match(self.path.split("?")[0])
            if not match:
                continue
            body = {}
            if method in ("POST", "PUT", "PATCH"):
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length) if length else b""
                try:
                    body = json.loads(raw.decode("utf-8")) if raw else {}
                except ValueError:
                    self._send(400, {"code": 400, "message": "请求体不是合法 JSON"})
                    return
            status, payload = handler(match, body)
            self._send(status, payload)
            return
        self._send(404, {"code": 404, "message": f"未找到 {method} {self.path}"})

    def _send(self, status, payload):
        if status == 204:
            self.send_response(204)
            self.end_headers()
            return
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self): self._dispatch("GET")
    def do_POST(self): self._dispatch("POST")
    def do_PUT(self): self._dispatch("PUT")
    def do_DELETE(self): self._dispatch("DELETE")
    def log_message(self, *args): pass


def request(method, url, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = Request(url, data=data, method=method,
                  headers={"Content-Type": "application/json"})
    try:
        with urlopen(req) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw.decode("utf-8")) if raw else None
    except HTTPError as exc:
        raw = exc.read()
        return exc.code, json.loads(raw.decode("utf-8")) if raw else None


def main():
    global DB_PATH
    with tempfile.TemporaryDirectory() as tmp:
        DB_PATH = str(Path(tmp) / "tasks.db")
        with get_conn() as conn:
            conn.execute("""
                CREATE TABLE tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    priority INTEGER NOT NULL DEFAULT 3,
                    done INTEGER NOT NULL DEFAULT 0
                )
            """)
            conn.commit()

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_address[1]}"

        try:
            print("创建：", request("POST", base + "/tasks", {"title": "写周报", "priority": 1}))
            print("创建：", request("POST", base + "/tasks", {"title": "买咖啡"}))
            print("列表：", request("GET", base + "/tasks")[1]["data"])
            print("详情：", request("GET", base + "/tasks/1"))
            print("更新：", request("PUT", base + "/tasks/1", {"done": True}))
            print("删除：", request("DELETE", base + "/tasks/2")[0])
            print("删除后查：", request("GET", base + "/tasks/2"))
            print("非法参数：", request("POST", base + "/tasks", {"title": "x", "priority": 9}))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


main()

# ===== 练习题 =====
# 1. 增加 PATCH /tasks/1/status 只改完成状态。
# 2. 列表接口支持 ?done=1 过滤（注意参数化查询）。
# 3. 给 tasks 表加 created_at，并让列表按创建时间倒序。
# 4. 思考：为什么每个请求都新建连接，而不是全局共享一个？
