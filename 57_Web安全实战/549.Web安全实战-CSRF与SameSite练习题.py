# ===== 第549课：Web安全实战-CSRF与SameSite =====
# 知识点：
#   - CSRF：攻击者诱导已登录用户在自己不知情下向目标站点发请求
#   - 条件：浏览器自动带 Cookie + 服务端只靠 Cookie 识别身份
#   - 防御 1：CSRF Token（同步令牌）——表单/请求头带随机 token，服务端校验
#   - 防御 2：SameSite Cookie（Strict/Lax）——跨站请求不自动带 Cookie
#   - 防御 3：校验 Origin/Referer；危险操作要求二次确认
#   - Token 要绑定会话、一次性或短时有效、用 compare_digest 比较（第268课）
#   - GET 不应修改数据（避免被图片/链接触发）
# 依赖：无（secrets/hmac 标准库）

import hmac
import secrets


class Session:
    def __init__(self, sid: str):
        self.sid = sid
        self.csrf_token = secrets.token_urlsafe(24)

    def check_csrf(self, token: str) -> bool:
        if not token:
            return False
        return hmac.compare_digest(self.csrf_token, token)


sessions: dict[str, Session] = {}


def login(user: str) -> tuple[str, Session]:
    sid = secrets.token_urlsafe(32)
    session = Session(sid)
    sessions[sid] = session
    return sid, session


def transfer(sid: str, csrf_token: str, amount: float) -> dict:
    """状态变更接口：必须同时有有效会话 + CSRF Token。"""
    session = sessions.get(sid)
    if session is None:
        return {"status": 401, "message": "未登录"}
    if not session.check_csrf(csrf_token):
        return {"status": 403, "message": "CSRF 校验失败"}
    return {"status": 200, "message": f"转账 {amount} 元成功"}


print("== 正常流程 ==")
sid, session = login("小明")
print("  登录 sid：", sid[:10], "…")
print("  CSRF Token：", session.csrf_token[:12], "…")
print("  带正确 Token：", transfer(sid, session.csrf_token, 100))

print("\n== 攻击场景：攻击者页面自动提交请求 ==")
print("  攻击者拿不到 Token（跨域读不到页面内容），请求头里没有 Token：")
print("  ", transfer(sid, "", 9999))
print("  伪造 Token：")
print("  ", transfer(sid, "fake-token", 9999))

# ---- SameSite 的作用 ----
print("\n== SameSite Cookie ==")
rows = [
    ("Strict", "任何跨站请求都不带 Cookie", "最安全，但外链进来会掉登录"),
    ("Lax", "顶层导航 GET 带，跨站 POST 不带", "默认值，兼顾体验"),
    ("None", "总是带（必须同时 Secure）", "跨站嵌入需要，风险最高"),
]
print(f"  {'值':<8}{'行为':<30}{'说明'}")
for r in rows:
    print(f"  {r[0]:<8}{r[1]:<30}{r[2]}")
print("  推荐：SameSite=Lax 作为默认；敏感操作再加 Token")

# ---- 为什么 Token 有效 ----
print("\n== Token 为什么有效 ==")
for item in [
    "攻击者站点无法读取目标站点的响应（同源策略）",
    "Token 不在 Cookie 里自动发送，攻击者拿不到",
    "Token 绑定会话，校验时用恒定时间比较",
    "Token 应一次性或短时有效，降低泄露风险",
]:
    print("  -", item)

# ---- 其他校验 ----
print("\n== Origin/Referer 校验 ==")
def check_origin(origin: str | None, allowed: set[str]) -> bool:
    return origin in allowed


allowed_origins = {"https://example.com", "https://www.example.com"}
for origin in ("https://example.com", "https://evil.com", None):
    print(f"  Origin={origin!r} → {'通过' if check_origin(origin, allowed_origins) else '拒绝'}")
print("  Origin 可能缺失（旧浏览器/隐私模式），所以只能作为辅助")

# ---- GET 与 POST ----
print("\n== 方法语义 ==")
print("  GET：只读，不应修改数据（否则<img src>就能触发）")
print("  POST/PUT/DELETE：修改数据，必须带 CSRF Token")

# ---- 常见错误 ----
print("\n== 常见错误 ==")
for item in [
    "把 Token 放在 URL 查询串里（会进日志/Referer 泄露）",
    "Token 全局固定，不绑定会话",
    "只用 SameSite 不做 Token（老浏览器可能不支持）",
    "用 GET 做删除/转账",
    "校验失败仍继续执行（必须 return）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给 transfer 增加“一次性 Token”：用后即失效。
# 2. 模拟攻击者带上了受害者 Cookie 但没有 Token，验证 403。
# 3. 设计一个同时支持表单和 JSON API 的 CSRF 方案。
# 4. 思考：为什么“验证 Referer”不能单独作为 CSRF 防御？
