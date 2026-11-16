# ===== 第706课：密码学协议进阶-综合案例-简易安全消息协议 =====
# 知识点：
#   - 综合串起本章：KDF -> DH 协商 -> 挑战应答 -> HMAC 认证 -> Merkle 审计 -> 承诺
#   - 一条消息的安全属性：机密性(加密)、完整性(MAC)、认证(签名)、不可否认(审计)
#   - 分层：握手（协商会话密钥）-> 传输（加密+认证）-> 审计（Merkle 日志）
#   - 加密用「玩具流密码」（HMAC 派生 keystream 异或），仅演示结构，明确标注非安全
#   - 每次会话用临时 DH 私钥（前向保密），nonce 一次性防重放
#   - 全部标准库 + 可注入时钟/随机数，纯内存演示，离线可运行
# 依赖：无（标准库）
import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass, field


def h(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

def kdf(shared: int, context: bytes) -> bytes:
    """从 DH 共享值派生会话密钥（HKDF 简化版）。"""
    return h(b"kdf" + context + str(shared).encode())

def keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    """教学用流密码：分块 HMAC 生成 keystream。绝不可用于生产。"""
    out = bytearray()
    counter = 0
    while len(out) < length:
        out += hmac.new(key, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest()
        counter += 1
    return bytes(out[:length])

def xor_crypt(data: bytes, key: bytes, nonce: bytes) -> bytes:
    ks = keystream(key, nonce, len(data))
    return bytes(a ^ b for a, b in zip(data, ks))

def mac(key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha256).digest()


@dataclass
class Session:
    key: bytes
    peer: str
    send_nonce: int = 0
    seen_nonces: set = field(default_factory=set)
    audit: list = field(default_factory=list)


@dataclass
class Envelope:
    sender: str
    seq: int
    ts: float
    nonce: bytes
    ciphertext: bytes
    tag: bytes

    def to_bytes(self):
        import json
        return json.dumps({
            "sender": self.sender, "seq": self.seq, "ts": self.ts,
            "nonce": self.nonce.hex(), "ciphertext": self.ciphertext.hex(),
            "tag": self.tag.hex(),
        }, sort_keys=True).encode()

    @classmethod
    def from_bytes(cls, raw):
        import json
        d = json.loads(raw)
        return cls(d["sender"], d["seq"], d["ts"], bytes.fromhex(d["nonce"]),
                   bytes.fromhex(d["ciphertext"]), bytes.fromhex(d["tag"]))


def seal(session, plaintext: str, now=None):
    """加密 + 认证，返回 Envelope。"""
    session.send_nonce += 1
    seq, ts = session.send_nonce, (now if now is not None else time.time())
    nonce = secrets.token_bytes(16)
    ct = xor_crypt(plaintext.encode("utf-8"), session.key, nonce)
    header = f"{session.peer}|{seq}|{ts}|".encode() + nonce
    tag = mac(session.key, header + ct)
    return Envelope(session.peer, seq, ts, nonce, ct, tag)


def open_envelope(session, env, now=None, skew=30.0):
    """验时间戳、验 nonce 重放、验 MAC，最后才解密。顺序不能反。"""
    now = now if now is not None else time.time()
    if abs(now - env.ts) > skew:
        return None, "时间戳超出窗口"
    if env.seq in session.seen_nonces:
        return None, "重放：序号已见过"
    header = f"{env.sender}|{env.seq}|{env.ts}|".encode() + env.nonce
    expected = mac(session.key, header + env.ciphertext)
    if not hmac.compare_digest(expected, env.tag):
        return None, "MAC 校验失败：数据被篡改或密钥不对"
    session.seen_nonces.add(env.seq)
    pt = xor_crypt(env.ciphertext, session.key, env.nonce).decode("utf-8")
    return pt, "OK"


# ---- Merkle 审计摘要（第705课） ----
class AuditLog:
    def __init__(self): self.records = []
    def add(self, env):
        self.records.append(h(env.to_bytes()))
    def root(self):
        cur = self.records[:] or [h(b"empty")]
        while len(cur) > 1:
            if len(cur) % 2: cur = cur + [cur[-1]]
            cur = [h(b"\x01" + cur[i] + cur[i + 1]) for i in range(0, len(cur), 2)]
        return cur[0]


print("== 1) DH 握手：协商会话密钥（前向保密）==")
P, G = 2**127 - 1, 2          # 教学用大素数（真实用标准群）
a, b = secrets.randbelow(P - 2) + 2, secrets.randbelow(P - 2) + 2
A, B = pow(G, a, P), pow(G, b, P)
sa, sb = pow(B, a, P), pow(A, b, P)
print(f"  共享值一致: {sa == sb}")
ka, kb = kdf(sa, b"alice-bob-v1"), kdf(sb, b"alice-bob-v1")
print(f"  派生会话密钥一致: {hmac.compare_digest(ka, kb)}  key={ka.hex()[:24]}...")
print("  每次会话重选 a/b -> 长期身份密钥泄露也推不出历史会话")

alice, bob = Session(ka, "Alice"), Session(kb, "Alice")
# Bob 端看到的 sender 也是 Alice，这里简化为双向各建一个会话
bob.peer = "Bob"

print("\n== 2) 挑战应答：Bob 确认 Alice 持有密钥 ==")
nonce = secrets.token_hex(16)
resp = hmac.new(ka, nonce.encode(), hashlib.sha256).hexdigest()
expect = hmac.new(kb, nonce.encode(), hashlib.sha256).hexdigest()
print(f"  nonce={nonce[:16]}...  认证通过={hmac.compare_digest(resp, expect)}")

print("\n== 3) 发送加密消息 ==")
now = 1_700_000_000.0
messages = ["转账 100 元", "确认收款", "会话结束"]
audit = AuditLog()
for m in messages:
    env = seal(alice, m, now=now)
    audit.add(env)
    pt, status = open_envelope(bob, env, now=now)
    print(f"  #{env.seq} {m!r:<16} -> 密文 {env.ciphertext.hex()[:24]}... "
          f"解密={pt!r} 状态={status}")

print("\n== 4) 攻击演示：篡改 / 重放 / 错密钥 ==")
env = seal(alice, "转账 100 元", now=now)
tampered = Envelope(env.sender, env.seq, env.ts, env.nonce,
                    bytes([env.ciphertext[0] ^ 1]) + env.ciphertext[1:], env.tag)
print("  改 1 个密文字节:", open_envelope(bob, tampered, now=now)[1])
env2 = seal(alice, "转账 100 元", now=now)
open_envelope(bob, env2, now=now)
print("  原样重放      :", open_envelope(bob, env2, now=now)[1])
wrong = Session(kdf(sa + 1, b"alice-bob-v1"), "Alice")
print("  用错密钥解密  :", open_envelope(wrong, env2, now=now)[1])
print("  时间戳超时    :", open_envelope(bob, seal(alice, "x", now=now - 999), now=now)[1])

print("\n== 5) Merkle 审计根（防事后删改日志）==")
print(f"  {len(audit.records)} 条消息 -> root={audit.root().hex()[:32]}...")
audit.add(seal(alice, "追加一条", now=now))
print(f"  追加一条后     -> root={audit.root().hex()[:32]}...（根必变）")

print("\n== 6) 承诺：先锁定消息摘要，稍后公开 ==")
salt = secrets.token_bytes(16)
commitment = h(salt + "结算结果=通过".encode())
print(f"  承诺={commitment.hex()[:32]}...（先公布）")
print(f"  打开验证={hmac.compare_digest(h(salt + '结算结果=通过'.encode()), commitment)}")
print(f"  抵赖成失败={hmac.compare_digest(h(salt + '结算结果=失败'.encode()), commitment)}")

print("\n== 分层回顾 ==")
for line in [
    "  KDF        : 把 DH 共享值变成均匀会话密钥（第699课）",
    "  DH         : 临时私钥协商，提供前向保密（第700课）",
    "  挑战应答   : 证明持有密钥，nonce 防重放（第701课）",
    "  加密 + MAC : 先验 MAC 再解密（encrypt-then-MAC）",
    "  Merkle     : 日志聚合为单个根，防事后篡改（第705课）",
    "  承诺       : 先锁定后公开，binding + hiding（第702课）",
]:
    print("  -", line)

print("\n== 教学实现的边界（务必阅读）==")
for line in [
    "  xor_crypt 是玩具流密码，绝不可用于生产",
    "  无证书/无身份认证，裸 DH 会被中间人攻击（第700课）",
    "  真实方案：X25519 + HKDF + AES-GCM/ChaCha20-Poly1305 + 签名证书",
    "  直接用 TLS 1.3 / libsodium / cryptography，别自己拼协议",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给 Envelope 增加接收方字段与会话 ID，防止跨会话重放。
# 2. 用第704课的玩具 RSA 为 DH 公钥签名，堵住中间人攻击。
# 3. 实现「密钥轮换」：每 N 条消息重新做一次 DH 握手。
# 4. 思考：为什么必须「先验 MAC 再解密」，反过来有什么风险？
