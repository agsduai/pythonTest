# ===== 第551课：Web安全实战-JWT签名与校验 =====
# 知识点：
#   - JWT = Base64Url(Header) + "." + Base64Url(Payload) + "." + Signature
#   - Header 声明算法（HS256），Payload 放 sub/exp/iat 等声明，Signature 防篡改
#   - HS256：HMAC-SHA256(header.payload, secret)，与第267课一致
#   - 校验必须：签名正确、算法符合预期、未过期、issuer/audience 匹配
#   - 常见漏洞：信任 header 里的 alg（改成 none 绕过）、不校验 exp、密钥泄露
#   - JWT 是“签名”不是“加密”：payload 任何人都能解码看到，别放敏感信息
#   - 与第550课会话 Cookie 的取舍：无状态 vs 可撤销
# 依赖：无（base64/hmac/json 标准库）

import base64
import hashlib
import hmac
import json
import time


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_decode(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def sign_jwt(payload: dict, secret: str, alg: str = "HS256") -> str:
    if alg != "HS256":
        raise ValueError("本课只支持 HS256")
    header = {"alg": alg, "typ": "JWT"}
    header_part = b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_part = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_part}.{payload_part}".encode()
    signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    return f"{header_part}.{payload_part}.{b64url_encode(signature)}"


def verify_jwt(token: str, secret: str) -> dict:
    try:
        header_part, payload_part, signature_part = token.split(".")
    except ValueError:
        raise ValueError("Token 格式错误")

    header = json.loads(b64url_decode(header_part))
    if header.get("alg") != "HS256":          # 关键：不接受 none/其他算法
        raise ValueError(f"不支持的算法：{header.get('alg')}")

    signing_input = f"{header_part}.{payload_part}".encode()
    expected = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    actual = b64url_decode(signature_part)
    if not hmac.compare_digest(expected, actual):
        raise ValueError("签名校验失败")

    payload = json.loads(b64url_decode(payload_part))
    if "exp" in payload and time.time() > payload["exp"]:
        raise ValueError("Token 已过期")
    return payload


SECRET = "demo-secret-key-do-not-commit"        # 实际从环境变量读取（第402课）
now = int(time.time())
token = sign_jwt({"sub": "user-1", "role": "user", "iat": now, "exp": now + 3600}, SECRET)

print("== 生成 Token ==")
print("  ", token[:60], "…")
print("  段数：", len(token.split(".")))

print("\n== 校验通过 ==")
payload = verify_jwt(token, SECRET)
print("  ", payload)

# ---- 查看 payload（JWT 不是加密！）----
print("\n== Payload 是明文 ==")
middle = token.split(".")[1]
print("  解码：", json.loads(b64url_decode(middle)))
print("  所以绝不能在 payload 里放密码/身份证号")

# ---- 篡改 payload ----
print("\n== 篡改 payload ==")
header_part, _, sig_part = token.split(".")
forged_payload = b64url_encode(json.dumps(
    {"sub": "admin", "role": "admin", "exp": now + 3600},
    separators=(",", ":"),
).encode())
forged = f"{header_part}.{forged_payload}.{sig_part}"
try:
    verify_jwt(forged, SECRET)
except ValueError as exc:
    print("  拦截：", exc)

# ---- 错误密钥 ----
print("\n== 错误密钥 ==")
try:
    verify_jwt(token, "wrong-secret")
except ValueError as exc:
    print("  拦截：", exc)

# ---- 过期 ----
print("\n== 过期 Token ==")
expired = sign_jwt({"sub": "user-1", "exp": int(time.time()) - 10}, SECRET)
try:
    verify_jwt(expired, SECRET)
except ValueError as exc:
    print("  拦截：", exc)

# ---- alg=none 攻击演示 ----
print("\n== alg=none 攻击 ==")
none_header = b64url_encode(json.dumps({"alg": "none", "typ": "JWT"}).encode())
none_token = f"{none_header}.{forged_payload}."
try:
    verify_jwt(none_token, SECRET)
except ValueError as exc:
    print("  拦截：", exc)
print("  防御：服务端固定允许的算法，绝不根据 header 选择")

# ---- JWT 使用清单 ----
print("\n== 使用清单 ==")
for item in [
    "密钥足够长且随机，放环境变量/密钥管理",
    "固定算法白名单，拒绝 none",
    "校验 exp/iat/nbf，时钟偏差留少量余量",
    "校验 iss/aud（多服务场景）",
    "Payload 不放敏感信息（只放 sub/role/exp）",
    "撤销难：短有效期 + 刷新令牌，或维护黑名单",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给 verify_jwt 增加 iss/aud 校验参数。
# 2. 实现 refresh token（长效、可撤销）与 access token（短效）配对。
# 3. 比较 HS256 与 RS256 的适用场景。
# 4. 思考：为什么“JWT 放 localStorage”容易被 XSS 窃取？放 Cookie 又有什么问题？
