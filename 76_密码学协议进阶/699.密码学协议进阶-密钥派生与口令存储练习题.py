# ===== 第699课：密码学协议进阶-密钥派生与口令存储 =====
# 知识点：
#   - 绝不明文存口令；也不要只用 sha256(password)（可被彩虹表/暴力破解）
#   - 盐 salt：每个口令独立随机值，使相同口令哈希不同，防预计算表
#   - KDF（密钥派生函数）故意「慢」：hashlib.pbkdf2_hmac / scrypt 拉高攻击成本
#   - 参数要随算法演进：迭代次数、盐长度、派生长度都应存进记录里
#   - 验证用 hmac.compare_digest 做常数时间比较，防时序侧信道
#   - 标准库无 argon2/bcrypt，生产建议 passlib/argon2-cffi；本课用 pbkdf2/scrypt 演示
# 依赖：无（标准库）
import hashlib
import hmac
import os
import secrets
import time

print("== 反面教材：裸哈希 ==")
a = hashlib.sha256(b"123456").hexdigest()
b = hashlib.sha256(b"123456").hexdigest()
print(f"  同一口令两次 sha256 完全相同: {a == b}  ({a[:24]}...)")
print("  -> 相同口令可一眼看出，且能被彩虹表直接反查")

print("\n== 加盐：相同口令产生不同哈希 ==")
def naive_salted(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    dk = hashlib.sha256(salt + password.encode()).digest()
    return salt, dk

for _ in range(2):
    salt, dk = naive_salted("123456")
    print(f"  salt={salt.hex()[:16]}... dk={dk.hex()[:24]}...")
print("  注意：salt 不需要保密，但必须随机且每条记录独立")

print("\n== PBKDF2：用迭代次数拖慢暴力破解 ==")
def pbkdf2_derive(password, salt=None, iterations=100_000, dklen=32):
    salt = salt or secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations, dklen)
    return {"alg": "pbkdf2_hmac_sha256", "salt": salt.hex(),
            "iterations": iterations, "dklen": dklen, "hash": dk.hex()}

rec = pbkdf2_derive("correct horse battery staple")
print("  记录字段:", {k: (v[:24] + "..." if isinstance(v, str) and len(v) > 30 else v)
                   for k, v in rec.items()})
print("  记录里不含口令，且带参数 -> 未来可平滑升级算法")

print("\n== 迭代次数的成本（可观测的「慢」）==")
for it in (10_000, 50_000, 100_000, 200_000):
    t0 = time.perf_counter()
    hashlib.pbkdf2_hmac("sha256", b"pw", b"0" * 16, it, 32)
    dt = (time.perf_counter() - t0) * 1000
    print(f"  iterations={it:>7} -> {dt:>7.1f} ms/次")
print("  服务端按「单次约 100~500ms」选参数，并在硬件升级后调高")

print("\n== scrypt：内存硬（memory-hard）==")
t0 = time.perf_counter()
sk = hashlib.scrypt(b"pw", salt=b"0" * 16, n=2**13, r=8, p=1, dklen=32)
print(f"  scrypt(n=2^13,r=8,p=1) 耗时 {(time.perf_counter()-t0)*1000:.1f} ms")
print(f"  派生结果 {sk.hex()[:32]}...（同时吃 CPU 与内存，GPU/ASIC 优势小）")

print("\n== 验证：常数时间比较 ==")
def verify(password, record):
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(),
                             bytes.fromhex(record["salt"]),
                             record["iterations"], record["dklen"])
    return hmac.compare_digest(dk, bytes.fromhex(record["hash"]))

for pw in ("correct horse battery staple", "wrong", "correct horse battery staplE"):
    print(f"  {pw[:28]!r:<32} -> {verify(pw, rec)}")

print("\n== 时序比较：普通 == 会提前返回 ==")
secret = b"a" * 32
guess_prefix = b"a" * 31 + b"b"
print("  hmac.compare_digest 逐字节比完再返回，不泄露「前几位对了」")
print("  普通 == 在第一个不同字节就停，理论上可被计时攻击利用")

print("\n== 口令策略与迁移 ==")
for line in [
    "  注册: 生成新 salt -> 派生 -> 存 {alg, salt, params, hash}",
    "  登录: 按记录里的参数重新派生 -> compare_digest",
    "  升级: 用户登录成功时，用新参数重算并覆盖旧记录",
    "  不要自己设计哈希；argon2id > scrypt > bcrypt > pbkdf2",
]:
    print("  -", line)

print("\n== 常见错误清单 ==")
for line in (
    "  ✗ 用 md5/sha1     : 太快且已不安全",
    "  ✗ 全局固定 salt   : 又变回「相同口令相同哈希」",
    "  ✗ salt 太短/可预测: 失去防预计算的意义",
    "  ✗ 用 == 比较哈希  : 时序侧信道",
    "  ✗ 把口令写进日志  : 直接泄露",
):
    print(" ", line)

# ===== 练习题 =====
# 1. 实现 needs_rehash(record, target_iterations)，登录时自动升级弱参数。
# 2. 对比 pbkdf2 / scrypt / blake2b 在相同耗时预算下的参数选择。
# 3. 写个「口令强度 + 泄露检测」的组合校验（本地字典，不联网）。
# 4. 思考：为什么 salt 可以明文存，而 pepper（全局密钥）必须单独保管？
