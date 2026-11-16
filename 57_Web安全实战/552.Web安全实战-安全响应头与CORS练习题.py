# ===== 第552课：Web安全实战-安全响应头与CORS =====
# 知识点：
#   - 安全响应头是“低成本高收益”的防线，浏览器据此限制攻击面
#   - CSP：限制脚本/样式/图片来源，缓解 XSS
#   - X-Content-Type-Options: nosniff：禁止浏览器猜类型
#   - X-Frame-Options / frame-ancestors：防点击劫持
#   - Referrer-Policy：控制 Referer 泄露
#   - HSTS：强制 HTTPS（Strict-Transport-Security）
#   - Permissions-Policy：禁用不需要的浏览器能力（摄像头/定位）
#   - CORS：跨域读取的许可机制；不要用 Access-Control-Allow-Origin: * 配凭证
# 依赖：无


def security_headers(https: bool = True) -> dict[str, str]:
    headers = {
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none'"
        ),
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        "Cross-Origin-Opener-Policy": "same-origin",
    }
    if https:
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return headers


print("== 推荐安全响应头 ==")
for name, value in security_headers().items():
    print(f"  {name}: {value}")

# ---- 每个头的威胁 ----
print("\n== 各头的防护目标 ==")
rows = [
    ("CSP", "XSS、恶意资源加载"),
    ("nosniff", "MIME 混淆攻击"),
    ("X-Frame-Options", "点击劫持（iframe 覆盖）"),
    ("Referrer-Policy", "URL 中的敏感参数泄露"),
    ("HSTS", "SSL stripping / 降级到 HTTP"),
    ("Permissions-Policy", "恶意调用摄像头/定位"),
    ("COOP", "跨窗口引用攻击（Spectre 类）"),
]
print(f"  {'响应头':<22}{'防什么'}")
for r in rows:
    print(f"  {r[0]:<22}{r[1]}")

# ---------------- CORS ----------------
print("\n== CORS：跨域读取许可 ==")


def cors_headers(origin: str | None, allowed_origins: set[str],
                 credentials: bool = True) -> dict[str, str]:
    if origin is None or origin not in allowed_origins:
        return {}                                    # 不回 CORS 头 → 浏览器拦截
    headers = {
        "Access-Control-Allow-Origin": origin,       # 回显具体来源，不用 *
        "Vary": "Origin",                            # 缓存要区分来源
    }
    if credentials:
        headers["Access-Control-Allow-Credentials"] = "true"
    return headers


ALLOWED = {"https://app.example.com", "https://admin.example.com"}

print("  允许的来源：")
for origin in ("https://app.example.com", "https://evil.com", None):
    h = cors_headers(origin, ALLOWED)
    print(f"    {str(origin):<32} → {h.get('Access-Control-Allow-Origin', '拒绝')}")

print("\n  预检请求（OPTIONS）应返回：")
preflight = {
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
    "Access-Control-Allow-Headers": "Content-Type, X-CSRF-Token",
    "Access-Control-Max-Age": "600",
}
for k, v in preflight.items():
    print(f"    {k}: {v}")

print("\n== CORS 常见错误 ==")
for item in [
    "Access-Control-Allow-Origin: * 同时 Allow-Credentials: true（浏览器禁止）",
    "按请求 Origin 无条件回显（等于允许所有站点）",
    "只校验 Origin 前缀（https://example.com.evil.com 绕过）",
    "预检通过后不做实际权限校验（CORS 不是认证）",
]:
    print("  -", item)

# ---------------- 组合示例 ----------------
print("\n== 一个安全响应示例 ==")
response = {
    "Content-Type": "application/json; charset=utf-8",
    **security_headers(),
    **cors_headers("https://app.example.com", ALLOWED),
}
for k, v in response.items():
    print(f"  {k}: {v}")

# ---- 落地建议 ----
print("\n== 落地建议 ==")
for item in [
    "安全头在反向代理/框架层统一加，避免漏接口",
    "CSP 先用 Report-Only 观察，再逐步收紧",
    "HSTS 上线前确认全站 HTTPS，否则会锁死用户",
    "CORS 白名单精确到域名，不用通配符配凭证",
    "定期用安全头扫描工具检查线上响应",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给一个返回 HTML 的接口设计 CSP（允许本站脚本与内联样式）。
# 2. 实现 CORS 中间件：预检请求直接返回 204。
# 3. 解释 HSTS 的 max-age 与 includeSubDomains 风险。
# 4. 思考：CORS 为什么不能替代服务端权限校验？
