# ===== 第234课：常用标准库-random与secrets =====
# 知识点：
#   - random：伪随机数 —— random/randint/uniform/sample/shuffle/choices
#   - seed 固定种子：结果可复现，调试与测试专用
#   - secrets：密码学安全随机 —— 验证码、令牌必须用它
#   - 原则：游戏抽奖用 random，涉及安全用 secrets

import random
import secrets

random.seed(42)                    # 固定种子，每次运行结果一样
print(random.random())             # [0, 1) 浮点数
print(random.randint(1, 6))        # 掷骰子
print(random.uniform(1.5, 3.5))    # 区间浮点数

# 抽样与洗牌
deck = list(range(1, 11))
print("抽3张不重复：", random.sample(deck, 3))
random.shuffle(deck)               # 原地打乱
print("洗牌后：", deck)
print("抽1张：", random.choice(["石头", "剪刀", "布"]))

# 加权随机：模拟抽奖概率
result = random.choices(["普通", "稀有", "史诗"], weights=[70, 25, 5], k=10)
print("十连抽：", result)
print("概率分布：", {x: result.count(x) for x in ("普通", "稀有", "史诗")})

# secrets：安全场景（验证码、令牌、会话 ID）
print("十六进制令牌：", secrets.token_hex(8))
print("URL安全令牌：", secrets.token_urlsafe(16))
print("0~99 随机数：", secrets.randbelow(100))


def gen_code(length=6):
    """数字验证码：每一位独立、不可预测。"""
    return "".join(secrets.choice("0123456789") for _ in range(length))


print("验证码：", gen_code())

# ===== 练习题 =====
# 1. 模拟掷两个骰子 10000 次，统计点数和的分布（配合 Counter）。
# 2. 用 random.sample 从全班名单里随机点 3 名同学。
# 3. 写一个 secrets 版的 8 位“强密码”生成器（含字母数字符号）。
# 4. 思考：为什么验证码不能用 random.randint 生成？
