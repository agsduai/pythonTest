# ===== 第1057课：随机数与模拟-随机密码生成器 =====
# 知识点：
#   - string 模块：ascii_letters 全部字母、digits 数字、punctuation 符号
#   - random.choice 逐位随机 + join 拼接，是密码生成的标准写法
#   - 保证"必有某类字符"：每类先各抽 1 个，剩余位再随机，最后 shuffle
#   - 真实安全场景用 secrets 模块（加密级随机），random 仅适合演示

# 案例一：纯数字密码
import random
import string

code = "".join(random.choice(string.digits) for _ in range(6))
print(f"6 位数字密码：{code}")

# 案例二：字母 + 数字混合
chars = string.ascii_letters + string.digits
pwd = "".join(random.choice(chars) for _ in range(8))
print(f"8 位混合密码：{pwd}")

# 案例三：保证四类字符都有
# 场景：网站要求"至少含大小写、数字、符号各一"
def gen_password(length=12):
    if length < 4:
        raise ValueError("长度至少为 4 才能容纳四类字符")
    groups = [
        random.choice(string.ascii_lowercase),
        random.choice(string.ascii_uppercase),
        random.choice(string.digits),
        random.choice(string.punctuation),
    ]
    all_chars = string.ascii_letters + string.digits + string.punctuation
    groups += [random.choice(all_chars) for _ in range(length - 4)]
    random.shuffle(groups)  # 打乱，别让"必含字符"总在前面
    return "".join(groups)

print(f"强密码：{gen_password()}")
print(f"短强密码：{gen_password(8)}")

# 案例四：批量生成用户初始密码
# 场景：给 5 位新员工各发一个初始密码
for name in ["小张", "小李", "小王", "小赵", "小周"]:
    print(f"{name} 的初始密码：{gen_password(10)}")

# 案例五：安全提示 —— 正式环境用 secrets
import secrets  # 标准库的加密级随机
secure_token = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
print(f"secrets 生成的令牌：{secure_token}")
print("random 是伪随机可预测，密码/令牌必须用 secrets")

# ===== 练习题 =====
# 1. 生成一个 10 位密码，只含字母和数字，并打印它包含的数字个数。
# 2. 写函数 gen_code(prefix, n)：返回 f"{prefix}-{随机n位大写字母数字}"，生成 3 个 "VIP" 开头的卡号。
# 3. 写函数 check_strength(pwd)：返回密码强度（长度 <8 弱；含数字和字母中 / 含符号强），测试 3 个不同密码。
