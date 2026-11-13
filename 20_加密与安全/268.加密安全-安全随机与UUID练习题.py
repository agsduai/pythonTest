# ===== 第268课：加密安全-安全随机与UUID =====
# 知识点：
#   - secrets：密码学安全随机（第234课），令牌/密钥/API Key 必须用它
#   - compare_digest：恒定时间比较 —— == 会“提前退出”泄露信息
#   - uuid4：随机 UUID，做全局唯一 ID
#   - 原则：随机的东西参与安全决策时，只能用 secrets

import secrets
import string
import uuid

# UUID：全局唯一标识符
print("uuid4：", uuid.uuid4())
print("uuid4：", uuid.uuid4())        # 每次都不一样
print("uuid4 hex：", uuid.uuid4().hex)

# 安全令牌
print("会话令牌：", secrets.token_urlsafe(32))


def gen_api_key(length=32):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


print("API Key　：", gen_api_key())


print("API Key　：", gen_api_key())

# == 比较的隐患：提前退出会泄露“错了几位”
# 演示：compare_digest 无论输入什么都花同样时间（恒定时间）
real_token = secrets.token_hex(16)


def check_unsafe(user_input):
    return user_input == real_token       # 教学示意：真实场景别这么写


def check_safe(user_input):
    return secrets.compare_digest(user_input, real_token)


print("安全比较：", check_safe(real_token), check_safe("wrong"))
print("不安全比较：", check_unsafe(real_token), check_unsafe("wrong"))

# 一次性密码本式的取值：验证码每位独立
code = "".join(secrets.choice("0123456789") for _ in range(6))
print("6位验证码：", code)

# 抽奖密钥、盐、IV 等字节流
print("32字节密钥：", secrets.token_bytes(32).hex()[:32], "...")

# ===== 练习题 =====
# 1. 用 uuid4 给“订单”生成唯一编号，并取前 8 位做展示编号。
# 2. 编写函数 new_session()：返回 (session_id, token)，token 用 token_urlsafe。
# 3. 思考：random.seed(42) 后生成的“随机数”为什么绝不能用于安全？
# 4. 思考：为什么验证码要“每位独立随机”，而不是一个随机数除位拆开？
