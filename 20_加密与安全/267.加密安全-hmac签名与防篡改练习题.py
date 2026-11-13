# ===== 第267课：加密安全-hmac签名与防篡改 =====
# 知识点：
#   - hmac：带密钥的哈希 —— 既验证“没被改过”，又验证“来自持钥者”
#   - 普通哈希人人可算；hmac 没有密钥就算不出合法签名
#   - 场景：API 请求签名、下载链接防篡改、回调验签
#   - compare_digest：恒定时间比较，防时序攻击

import hashlib
import hmac
import json

SECRET_KEY = b"demo-secret-key"      # 实际项目放环境变量（第217课）


def sign(data: dict) -> str:
    """对数据签名：排序序列化保证同样数据得到同样签名。"""
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True)
    return hmac.new(SECRET_KEY, payload.encode("utf-8"), hashlib.sha256).hexdigest()


def verify(data: dict, signature: str) -> bool:
    return hmac.compare_digest(sign(data), signature)


# 正常流程：签名 → 传输 → 验签
order = {"order_id": "A001", "amount": 99}
sig = sign(order)
print("签名：", sig[:32], "...")
print("原数据验签：", verify(order, sig))

# 攻击1：篡改金额
tampered = dict(order, amount=1)
print("篡改金额后验签：", verify(tampered, sig))

# 攻击2：没有密钥，伪造不出合法签名
fake_sig = hmac.new(
    b"wrong-key", json.dumps(order, sort_keys=True).encode("utf-8"), hashlib.sha256
).hexdigest()
print("伪造签名验签：", verify(order, fake_sig))

# 为什么用 sort_keys=True：键顺序不同会导致签名不同
a = {"a": 1, "b": 2}
b = {"b": 2, "a": 1}
print("键顺序不同签名一致：", sign(a) == sign(b))

# 下载链接防篡改的典型拼法：文件名 + 过期时间 + 签名
expires = 1700000000
link_sig = hmac.new(SECRET_KEY, f"report.pdf-{expires}".encode(), hashlib.sha256).hexdigest()
print("带签名下载链接：/report.pdf?expires={}&sig={}...".format(expires, link_sig[:16]))

# ===== 练习题 =====
# 1. 给签名数据加入时间戳字段，实现“签名过期”校验。
# 2. 思考：为什么 verify 必须用 compare_digest 而不是 ==？（下一课演示）
# 3. 把 SECRET_KEY 改为从环境变量读取，缺失时报明确错误。
