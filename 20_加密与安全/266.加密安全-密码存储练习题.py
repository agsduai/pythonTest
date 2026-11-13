# ===== 第266课：加密安全-密码存储 =====
# 知识点：
#   - 明文存密码 = 事故；纯 md5 也远远不够（可被彩虹表反查）
#   - 加盐：给每个用户生成随机盐，相同密码哈希出不同结果
#   - 慢哈希 pbkdf2_hmac：故意慢，暴力破解代价高
#   - 存储格式：算法$迭代次数$盐$摘要
#   - 比较摘要用恒定时间比较（下一课细讲）

import hashlib
import secrets


def hash_password(password: str) -> str:
    """生成可存储的密码哈希。"""
    salt = secrets.token_bytes(16)                       # 每次随机盐
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"pbkdf2_sha256$100000${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """按存储格式还原参数，重算并比较。"""
    algo, iters, salt_hex, hash_hex = stored.split("$")
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iters)
    )
    return secrets.compare_digest(dk.hex(), hash_hex)


# 同一密码，两次哈希结果完全不同（盐的作用）
stored1 = hash_password("abc12345")
stored2 = hash_password("abc12345")
print("两次存储结果不同：", stored1 != stored2)
print("存储格式示例：", stored1[:60], "...")

# 验证：只认密码，不管盐
print("正确密码：", verify_password("abc12345", stored1))
print("错误密码：", verify_password("abc99999", stored1))
print("另一份存储也能验证：", verify_password("abc12345", stored2))

# 数据库用户表的模拟
users = {}     # username -> stored hash
users["小明"] = hash_password("python666")
users["小红"] = hash_password("python666")     # 同密码也不泄露“他们密码相同”
print("两人密码相同但存储不同：", users["小明"] != users["小红"])
print("登录成功：", verify_password("python666", users["小明"]))
print("登录失败：", verify_password("wrong", users["小红"]))

# ===== 练习题 =====
# 1. 把迭代次数改成 1000 和 300000，用 timeit 感受“故意慢”的差异。
# 2. 编写 register/login 两个函数，串成完整流程。
# 3. 思考：为什么盐可以明文存储？它防的是什么攻击？
# 4. 思考：忘了密码为什么只能“重置”而不能“找回”？
