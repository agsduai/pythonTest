# ===== 第406课：Web API 与接口测试-POST与参数校验 =====
# 知识点：
#   - POST 请求体：读 Content-Length → rfile.read → json.loads
#   - Content-Type: application/json 是约定，服务端应据此解析
#   - 校验分层：格式（JSON 是否合法）→ 必填 → 类型 → 业务规则
#   - 错误响应带字段级明细：{"errors": {"age": "必须在 0~150"}}
#   - 成功创建返回 201 + Location 头（指向新资源）
# 依赖：无（标准库）

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

users = {}                 # 内存存储：id -> dict
next_id = [1]


def validate_user(payload: dict) -> dict:
    """返回字段级错误字典；空字典表示通过。"""
    errors = {}
    name = payload.get("name")
    if not isinstance(name, str) or not name.strip():
        errors["name"] = "姓名必填且必须是非空字符串"
    elif len(name) > 20:
        errors["name"] = "姓名不能超过 20 个字符"

    age = payload.get("age")
    if age is None or isinstance(age, bool) or not isinstance(age, int):
        errors["age"] = "年龄必填且必须是整数"
    elif not (0 <= age <= 150):
        errors["age"] = "年龄必须在 0~150 之间"

    email = payload.get("email")
    if email is not None:
        if not isinstance(email, str) or "@" not in email:
            errors["email"] = "邮箱格式不正确"
    return errors


class Handler(BaseHTTPRequestHandler):

    def _send(self, status, payload, extra_headers=None):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/users":
            self._send(200, {"code": 0, "data": list(users.values())})
        else:
            self._send(404, {"code": 404, "message": "未找到"})

    def do_POST(self):
        if self.path != "/users":
            self._send(404, {"code": 404, "message": "未找到"})
            return

        # ---- 1. 读请求体 ----
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b""
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except (ValueError, UnicodeDecodeError) as exc:
            self._send(400, {"code": 400, "message": f"请求体不是合法 JSON：{exc}"})
            return

        if not isinstance(payload, dict):
            self._send(400, {"code": 400, "message": "请求体必须是 JSON 对象"})
            return

        # ---- 2. 校验 ----
        errors = validate_user(payload)
        if errors:
            self._send(422, {"code": 422, "message": "参数校验失败", "errors": errors})
            return

        # ---- 3. 保存 ----
        user_id = next_id[0]
        next_id[0] += 1
        user = {"id": user_id, **payload}
        users[user_id] = user

        self._send(
            201,
            {"code": 0, "message": "创建成功", "data": user},
            extra_headers={"Location": f"/users/{user_id}"},
        )

    def log_message(self, *args):
        pass


def start():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, server.server_address[1]


def post_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlopen(request) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8")), dict(resp.headers)
    except HTTPError as exc:                    # 4xx/5xx 走 HTTPError
        return exc.code, json.loads(exc.read().decode("utf-8")), dict(exc.headers)


server, thread, port = start()
base = f"http://127.0.0.1:{port}"
try:
    print("== 正常创建 ==")
    status, body, headers = post_json(base + "/users", {"name": "小明", "age": 18,
                                                        "email": "ming@example.com"})
    print(status, body, "| Location:", headers.get("Location"))

    print("\n== 校验失败 ==")
    status, body, _ = post_json(base + "/users", {"name": "", "age": 200, "email": "bad"})
    print(status, body)

    print("\n== 非法 JSON ==")
    request = Request(base + "/users", data=b"{not json",
                      headers={"Content-Type": "application/json"})
    try:
        urlopen(request)
    except HTTPError as exc:
        print(exc.code, json.loads(exc.read().decode("utf-8")))

    print("\n== 查询列表 ==")
    with urlopen(base + "/users") as resp:
        print(resp.status, json.loads(resp.read().decode("utf-8")))
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)

# ===== 练习题 =====
# 1. 给 validate_user 增加 phone 字段（11 位数字，可空）。
# 2. 重复邮箱应返回 409，请增加该业务校验。
# 3. 让错误响应包含 "field" 与 "message" 的结构化列表。
# 4. 思考：为什么“先格式、再必填、再业务”这个校验顺序最省事？
