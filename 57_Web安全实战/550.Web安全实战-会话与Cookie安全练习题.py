# ===== 第550课：Web安全实战-会话与Cookie安全 =====
# 知识点：
#   - 会话 ID 必须高熵（secrets.token_urlsafe，至少 128 位）
#   - Cookie 安全属性：
#     HttpOnly（JS 读不到，防 XSS 窃取）、Secure（只走 HTTPS）、
#     SameSite（防 CSRF）、Path、Max-Age
#   - 会话固定（Session Fixation）：登录后必须换新 SID
#   - 会话过期：空闲超时 + 绝对超时；登出要服务端销毁
#   - 不要在 URL 里放 SID；不要存敏感信息在 Cookie 明文里
#   - 与第549课 CSRF、第551课 JWT 的配合
# 依赖：无（secrets/time 标准库）

import hashlib
import secrets
import time


class SessionStore:
    def __init__(self, idle_timeout=1800, absolute_timeout=8 * 3600, clock=time.monotonic):
        self.sessions: dict[str, dict] = {}
        self.idle_timeout = idle_timeout
        self.absolute_timeout = absolute_timeout
        self.clock = clock

    def create(self, user: str) -> str:
        sid = secrets.token_urlsafe(32)          # 256 位熵
        now = self.clock()
        self.sessions[sid] = {
            "user": user,
            "created_at": now,
            "last_seen": now,
        }
        return sid

    def get(self, sid: str | None) -> dict | None:
        if not sid or sid not in self.sessions:
            return None
        session = self.sessions[sid]
        now = self.clock()
        if now - session["last_seen"] > self.idle_timeout:
            del self.sessions[sid]
            return None
        if now - session["created_at"] > self.absolute_timeout:
            del self.sessions[sid]
            return None
        session["last_seen"] = now
        return session

    def destroy(self, sid: str):
        self.sessions.pop(sid, None)

    def rotate(self, old_sid: str) -> str:
        """登录/提权后换新 SID，防会话固定。"""
        session = self.sessions.pop(old_sid, None)
        if session is None:
            raise KeyError("会话不存在")
        sid = secrets.token_urlsafe(32)
        session["created_at"] = self.clock()
        session["last_seen"] = self.clock()
        self.sessions[sid] = session
        return sid


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


clock = FakeClock()
store = SessionStore(idle_timeout=60, absolute_timeout=300, clock=clock)

print("== 创建会话 ==")
sid = store.create("小明")
print("  SID：", sid[:12], "…（长度", len(sid), "字符）")
print("  查询：", store.get(sid)["user"])

print("\n== 空闲超时 ==")
clock.advance(61)
print("  61 秒未操作：", store.get(sid))

print("\n== 绝对超时 ==")
clock2 = FakeClock()
store2 = SessionStore(idle_timeout=100, absolute_timeout=200, clock=clock2)
sid2 = store2.create("小红")
for t in (50, 100, 150):
    clock2.now = t
    print(f"  t={t}s 访问：", store2.get(sid2) is not None)
clock2.now = 201
print("  t=201s（超过绝对超时）：", store2.get(sid2))

print("\n== 会话固定攻击 ==")
# 攻击者预先给受害者一个已知 SID；受害者登录后若沿用该 SID，攻击者就能共用
attacker_sid = "attacker-known-sid"
store.sessions[attacker_sid] = {"user": "anonymous", "created_at": clock.now,
                                "last_seen": clock.now}
print("  受害者登录前 SID：", attacker_sid)
new_sid = store.rotate(attacker_sid)          # 登录成功 → 换新 SID
print("  登录后 SID：", new_sid[:12], "…（旧 SID 已失效）")
print("  攻击者用旧 SID：", store.get(attacker_sid))
print("  受害者用新 SID：", store.get(new_sid)["user"])

print("\n== Cookie 安全属性 ==")
cookie = (
    "sid=" + sid[:8] + "…; "
    "HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=1800"
)
print("  Set-Cookie:", cookie)
rows = [
    ("HttpOnly", "JS 无法读取，降低 XSS 窃取风险"),
    ("Secure", "只通过 HTTPS 发送，防中间人"),
    ("SameSite", "跨站请求不带，降低 CSRF 风险"),
    ("Max-Age", "浏览器侧过期，服务端仍要校验"),
]
print(f"  {'属性':<10}{'作用'}")
for r in rows:
    print(f"  {r[0]:<10}{r[1]}")

print("\n== 登出 ==")
store.destroy(new_sid)
print("  销毁后查询：", store.get(new_sid))
print("  说明：只清浏览器 Cookie 不够，服务端必须删除会话")

# ---- 存储建议 ----
print("\n== 存储建议 ==")
for item in [
    "SID 只存随机串，不存用户信息/权限（服务端查）",
    "需要跨实例共享 → Redis 等集中存储",
    "会话表加索引与过期清理任务",
    "管理员/敏感操作可缩短超时或要求二次验证",
    "不要把 SID 放 URL、日志、Referer 可见的位置",
]:
    print("  -", item)

# ---- 与 JWT 的取舍 ----
print("\n== 会话 Cookie vs JWT ==")
rows = [
    ("服务端会话", "可随时失效、实现简单", "需要存储、水平扩展要共享"),
    ("JWT", "无状态、跨服务方便", "撤销难、泄露后到期前都有效"),
]
print(f"  {'方案':<12}{'优点':<22}{'代价'}")
for r in rows:
    print(f"  {r[0]:<12}{r[1]:<22}{r[2]}")

# ===== 练习题 =====
# 1. 给 SessionStore 增加“清理所有过期会话”方法。
# 2. 模拟“记住我”：单独的长效 Token + 可撤销。
# 3. 给会话增加 IP/UA 绑定，评估误伤与安全收益。
# 4. 思考：JWT 泄露后为什么很难立即失效？如何缓解？
