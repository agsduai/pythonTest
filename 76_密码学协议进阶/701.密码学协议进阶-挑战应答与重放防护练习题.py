# ===== 第701课：密码学协议进阶-挑战应答与重放防护 =====
# 知识点：
#   - 挑战应答：服务端发随机 nonce，客户端用密钥算 HMAC(nonce) 作答
#   - 证明「持有密钥」而不传输密钥本身；每次 nonce 不同，响应也不同
#   - 重放攻击：攻击者录下旧响应原样重发；防法有 nonce 一次性、时间戳窗口、序号
#   - 双向认证：客户端也要给服务端发挑战，避免连到假冒服务器
#   - 所有比较用 hmac.compare_digest，避免时序泄露
#   - 本课用可注入时钟与 nonce 集合，纯内存演示，不联网
# 依赖：无（标准库）
import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass, field


@dataclass
class Server:
    secret: bytes
    used_nonces: set = field(default_factory=set)
    clock_skew: float = 30.0       # 允许的时间戳偏差（秒）

    def challenge(self):
        nonce = secrets.token_hex(16)
        self.used_nonces.add(nonce)
        return nonce

    def verify_nonce(self, nonce, response):
        """一次性 nonce：用过即失效，天然防重放。"""
        if nonce not in self.used_nonces:
            return False, "nonce 未签发或已用过"
        self.used_nonces.discard(nonce)
        expected = hmac.new(self.secret, nonce.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, response):
            return False, "响应不正确"
        return True, "通过"

    def verify_timestamp(self, ts, payload, response, now=None):
        """时间戳窗口：无需存 nonce，但要防窗口内的重放（配 jti 集合）。"""
        now = now if now is not None else time.time()
        if abs(now - ts) > self.clock_skew:
            return False, "时间戳超出允许窗口"
        msg = f"{ts}:{payload}".encode()
        expected = hmac.new(self.secret, msg, hashlib.sha256).hexdigest()
        return (hmac.compare_digest(expected, response), "通过" if
                hmac.compare_digest(expected, response) else "响应不正确")


def respond(secret, nonce):
    return hmac.new(secret, nonce.encode(), hashlib.sha256).hexdigest()


def sign_ts(secret, ts, payload):
    return hmac.new(secret, f"{ts}:{payload}".encode(), hashlib.sha256).hexdigest()


KEY = b"shared-secret-between-client-and-server"
print("== 挑战应答正常流程 ==")
srv = Server(KEY)
nonce = srv.challenge()
resp = respond(KEY, nonce)
print(f"  challenge nonce = {nonce}")
print(f"  response        = {resp[:32]}...")
print("  验证:", srv.verify_nonce(nonce, resp))

print("\n== 重放：同一响应再用一次 ==")
print("  立刻重放:", srv.verify_nonce(nonce, resp))
print("  -> nonce 验证通过后被丢弃，第二次必然失败")

print("\n== 错误密钥 / 篡改响应 ==")
n2 = srv.challenge()
print("  错误密钥:", srv.verify_nonce(n2, respond(b"wrong-key", n2)))
n3 = srv.challenge()
r3 = respond(KEY, n3)
tampered = r3[:-1] + ("0" if r3[-1] != "0" else "1")
print("  改 1 个字符:", srv.verify_nonce(n3, tampered))

print("\n== 时间戳方案（窗口 + jti 去重）==")
now = 1_700_000_000.0
ts = now
sig = sign_ts(KEY, ts, "transfer:100")
print("  窗口内:", srv.verify_timestamp(ts, "transfer:100", sig, now=now))
print("  超时 60s:", srv.verify_timestamp(ts - 60, "transfer:100",
                                         sign_ts(KEY, ts - 60, "transfer:100"), now=now))
print("  改金额:", srv.verify_timestamp(ts, "transfer:99999", sig, now=now))
print("  注意：窗口内仍可重放，需额外用 jti/nonce 集合去重")

print("\n== 双向认证 ==")
client_key, server_key = b"client-key", b"server-key"
cs, sc = Server(client_key), Server(server_key)
c_nonce, s_nonce = cs.challenge(), sc.challenge()
print("  客户端证明自己:", cs.verify_nonce(c_nonce, respond(client_key, c_nonce)))
print("  服务端证明自己:", sc.verify_nonce(s_nonce, respond(server_key, s_nonce)))
print("  只有单向认证时，客户端可能连到假冒服务端")

print("\n== nonce 生成要求 ==")
print("  用 secrets.token_hex(16)（CSPRNG），不要用 random / 时间戳 / 自增 ID")
print("  长度至少 128 bit，保证碰撞概率可忽略")
nonces = [secrets.token_hex(16) for _ in range(5)]
print("  示例:", [n[:12] + "..." for n in nonces])
print("  全不相同:", len(set(nonces)) == len(nonces))

print("\n== 三种防重放机制对比 ==")
print(f"  {'机制':<14}{'服务端状态':<16}{'时钟依赖':<10}{'适用场景'}")
for row in (("一次性 nonce", "存已签发集合", "无", "登录/一次性操作"),
            ("时间戳窗口", "存 jti 集合", "需同步", "API 请求"),
            ("递增序号", "存最大序号", "无", "长连接/消息流")):
    print(f"  {row[0]:<14}{row[1]:<16}{row[2]:<10}{row[3]}")

print("\n== 常见漏洞 ==")
for line in [
    "  用 random 生成 nonce -> 可预测，攻击者能预计算响应",
    "  只校验时间戳不校验签名 -> 随便改金额都能过",
    "  用 == 比较 HMAC -> 时序侧信道逐字节猜出正确值",
    "  nonce 永不失效 -> 数据库无限膨胀，且无法撤销",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给 Server 增加 jti 集合，堵住时间戳窗口内的重放。
# 2. 实现「递增序号 + 滑动窗口」，允许乱序到达但拒绝旧序号。
# 3. 把挑战应答改成双向：客户端也验证服务端对 nonce 的签名。
# 4. 思考：为什么时间戳方案必须同时做「窗口」与「去重」，缺一不可？
