# ===== 第554课：Web安全实战-综合案例-安全登录API =====
# 知识点：
#   - 综合运用：密码哈希（266）+ 会话/Cookie（550）+ CSRF（549）
#     + 限流（446）+ 安全响应头（552）+ 参数校验（406）
#   - 完整链路：注册（加盐慢哈希）→ 登录（限流+校验）→ 会话 Cookie
#     → 受保护接口（Cookie + CSRF Token）→ 安全响应头
#   - Cookie 设置 HttpOnly/SameSite；CSRF 用请求头传递
#   - 登录失败不区分“用户不存在/密码错误”，避免账号枚举
#   - 与第39章 REST、第44章可靠性、第57章安全直接配套
# 依赖：无（标准库）

import hashlib
import hmac
import json
import secrets
import threading
import time
from collections import defaultdict
from http.cookiejar import CookieJar
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener

USERS: dict[str, dict] = {}
SESSIONS: dict[str, dict] = {}
LOGIN_HISTORY: dict[str, list[float]] = defaultdict(list)
LOCK = threading.Lock()
SESSION_TTL = 3600
MAX_LOGIN_ATTEMPTS = 5
WINDOW = 60.0

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Cache-Control": "no-store",
}


def hash_password(password: str) -> tuple[bytes, bytes]:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return salt, digest


def verify_password(password: str, salt: bytes, expected: bytes) -> bool:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return hmac.compare_digest(digest, expected)


def create_session(user: str) -> tuple[str, str]:
    sid = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(24)
    SESSIONS[sid] = {"user": user, "csrf": csrf, "expires": time.time() + SESSION_TTL}
    return sid, csrf


def session_from_cookie(handler) -> tuple[str | None, dict | None]:
    raw = handler.headers.get("Cookie", "")
    for part in raw.split(";"):
        part = part.strip()
        if part.startswith("sid="):
            sid = part[4:]
            session = SESSIONS.get(sid)
            if session and session["expires"] > time.time():
                return sid, session
    return None, None


def rate_limited(ip: str) -> bool:
    now = time.time()
    history = [t for t in LOGIN_HISTORY[ip] if now - t < WINDOW]
    LOGIN_HISTORY[ip] = history
    return len(history) >= MAX_LOGIN_ATTEMPTS


class Handler(BaseHTTPRequestHandler):

    def _send(self, status: int, payload: dict, extra: dict | None = None):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for key, value in {**SECURITY_HEADERS, **(extra or {})}.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise ValueError("请求体不是合法 JSON")
        if not isinstance(data, dict):
            raise ValueError("请求体必须是 JSON 对象")
        return data

    def do_POST(self):
        try:
            body = self._read_json()
        except ValueError as exc:
            self._send(400, {"error": str(exc)})
            return

        if self.path == "/register":
            username = str(body.get("username", "")).strip()
            password = str(body.get("password", ""))
            if not (3 <= len(username) <= 20):
                self._send(422, {"error": "用户名长度 3~20"})
                return
            if len(password) < 8:
                self._send(422, {"error": "密码至少 8 位"})
                return
            with LOCK:
                if username in USERS:
                    self._send(409, {"error": "用户已存在"})
                    return
                salt, digest = hash_password(password)
                USERS[username] = {"salt": salt, "digest": digest}
            self._send(201, {"message": "注册成功"})
            return

        if self.path == "/login":
            ip = self.client_address[0]
            if rate_limited(ip):
                self._send(429, {"error": "登录尝试过于频繁，请稍后再试"})
                return
            username = str(body.get("username", ""))
            password = str(body.get("password", ""))
            user = USERS.get(username)
            if user is None or not verify_password(password, user["salt"], user["digest"]):
                LOGIN_HISTORY[ip].append(time.time())
                self._send(401, {"error": "用户名或密码错误"})   # 不区分原因
                return
            LOGIN_HISTORY[ip].clear()
            sid, csrf = create_session(username)
            cookie = f"sid={sid}; HttpOnly; SameSite=Strict; Path=/; Max-Age={SESSION_TTL}"
            self._send(200, {"message": "登录成功", "csrf_token": csrf},
                       extra={"Set-Cookie": cookie})
            return

        if self.path == "/transfer":
            sid, session = session_from_cookie(self)
            if session is None:
                self._send(401, {"error": "未登录"})
                return
            token = self.headers.get("X-CSRF-Token", "")
            if not hmac.compare_digest(token, session["csrf"]):
                self._send(403, {"error": "CSRF 校验失败"})
                return
            amount = body.get("amount")
            if not isinstance(amount, (int, float)) or amount <= 0:
                self._send(422, {"error": "金额必须为正数"})
                return
            self._send(200, {"message": f"{session['user']} 转账 {amount} 元成功"})
            return

        self._send(404, {"error": "接口不存在"})

    def do_GET(self):
        if self.path == "/me":
            sid, session = session_from_cookie(self)
            if session is None:
                self._send(401, {"error": "未登录"})
                return
            self._send(200, {"user": session["user"], "csrf_token": session["csrf"]})
            return
        if self.path == "/health":
            self._send(200, {"status": "ok"})
            return
        self._send(404, {"error": "接口不存在"})

    def log_message(self, *args):
        pass


def call(opener, method: str, url: str, payload=None, headers=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(url, data=data, method=method,
                      headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with opener.open(request) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw.decode("utf-8")) if raw else {}, dict(resp.headers)
    except HTTPError as exc:
        raw = exc.read()
        return exc.code, json.loads(raw.decode("utf-8")) if raw else {}, dict(exc.headers)


server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
base = f"http://127.0.0.1:{server.server_address[1]}"
opener = build_opener(HTTPCookieProcessor(CookieJar()))

try:
    print("== 注册 ==")
    print("  ", call(opener, "POST", base + "/register",
                    {"username": "alice", "password": "S3curePass!"}))
    print("  重复注册：", call(opener, "POST", base + "/register",
                          {"username": "alice", "password": "S3curePass!"})[0])
    print("  弱密码：", call(opener, "POST", base + "/register",
                         {"username": "bob", "password": "123"})[0])

    print("\n== 登录 ==")
    print("  错误密码：", call(opener, "POST", base + "/login",
                          {"username": "alice", "password": "wrong"})[0])
    status, body, headers = call(opener, "POST", base + "/login",
                                 {"username": "alice", "password": "S3curePass!"})
    print("  正确登录：", status, body["message"])
    print("  Set-Cookie：", headers.get("Set-Cookie", "")[:60], "…")
    csrf = body["csrf_token"]

    print("\n== 受保护接口 ==")
    print("  /me：", call(opener, "GET", base + "/me")[1])
    print("  无 CSRF 转账：", call(opener, "POST", base + "/transfer", {"amount": 100})[0])
    print("  伪造 CSRF：", call(opener, "POST", base + "/transfer", {"amount": 100},
                             {"X-CSRF-Token": "fake"})[0])
    print("  正确 CSRF：", call(opener, "POST", base + "/transfer", {"amount": 100},
                             {"X-CSRF-Token": csrf})[1])

    print("\n== 未登录访问 ==")
    anonymous = build_opener(HTTPCookieProcessor(CookieJar()))
    print("  /me：", call(anonymous, "GET", base + "/me")[0])

    print("\n== 登录限流（同 IP 连续失败）==")
    # 先清空历史（正确登录后已清空），连续错 5 次再试
    for i in range(5):
        call(opener, "POST", base + "/login", {"username": "alice", "password": "bad"})
    print("  第 6 次：", call(opener, "POST", base + "/login",
                          {"username": "alice", "password": "bad"})[0], "（429 = 限流）")

    print("\n== 安全响应头 ==")
    status, body, headers = call(opener, "GET", base + "/health")
    for key in ("X-Content-Type-Options", "X-Frame-Options", "Content-Security-Policy",
                "Cache-Control", "Referrer-Policy"):
        print(f"  {key}: {headers.get(key)}")
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)

# ---- 安全清单 ----
print("\n== 本案例覆盖的安全点 ==")
for item in [
    "密码：PBKDF2 + 随机盐 + 10 万次迭代（第266课）",
    "登录错误统一提示，避免账号枚举",
    "登录限流：同 IP 60 秒最多 5 次（第446课）",
    "会话：高熵 SID + 1 小时过期 + 服务端存储（第550课）",
    "Cookie：HttpOnly + SameSite=Strict（第550课）",
    "CSRF：请求头 Token + 恒定时间比较（第549课）",
    "响应头：nosniff / DENY / CSP / no-store（第552课）",
    "输入校验：用户名/密码/金额（第406课）",
]:
    print("  -", item)

# ---- 还可以加强 ----
print("\n== 生产环境还应加 ==")
for item in [
    "HTTPS + HSTS（第552课）",
    "注册邮箱/手机验证，防批量注册",
    "多因素认证（MFA）",
    "登录审计日志与异常告警（第417课）",
    "会话存储在 Redis，支持多实例与主动踢下线",
    "密码泄露检测（HaveIBeenPwned 等）",
    "WAF/验证码对抗撞库",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 增加 /logout，服务端销毁会话并清 Cookie。
# 2. 登录成功后轮换 SID（防会话固定）。
# 3. 给 /transfer 增加“转账金额上限”和“二次确认 Token”。
# 4. 思考：为什么登录失败不能提示“用户不存在”？
