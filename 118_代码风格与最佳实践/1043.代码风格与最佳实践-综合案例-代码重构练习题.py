# ===== 第1043课：代码风格与最佳实践-综合案例-代码重构 =====
# 知识点：
#   - 重构 = 不改功能，只让代码更好读、更好改
#   - 五板斧：改命名、提常量、拆函数、消灭魔法数字、换推导式
#   - 重构前先确认行为：跑一遍记下输出，重构后输出必须一致
#   - 小步重构：每改一处就运行验证，不要一口气全改完再测

# 案例一：重构前 —— 一段"能跑但没人想维护"的代码
def a(d):
    r = 0
    c = 0
    for x in d:
        if x > 0:
            r = r + x * 1.1
            c = c + 1
    if c > 0:
        t = r / c * 0.9
    else:
        t = 0
    return t

data = [100, 200, -50, 300]
print(f"重构前输出：{a(data):.2f}")

# 案例二：第一步改命名 —— 让名字说明意图
# d -> prices（原始价格），r -> discounted_sum，c -> valid_count
def b(prices):
    discounted_sum = 0
    valid_count = 0
    for price in prices:
        if price > 0:
            discounted_sum = discounted_sum + price * 1.1
            valid_count = valid_count + 1
    if valid_count > 0:
        result = discounted_sum / valid_count * 0.9
    else:
        result = 0
    return result

print(f"改命名后输出：{b(data):.2f}")  # 必须和重构前一致

# 案例三：第二步提常量 —— 神秘的 1.1 和 0.9 到底是什么
# 1.1 是"涨价 10%"，0.9 是"会员再打 9 折"
TAX_RATE = 1.1       # 含 10% 服务费
MEMBER_DISCOUNT = 0.9

# 案例四：第三步拆函数 —— 每个函数一件事
def filter_valid(prices):
    """只留正数价格。"""
    return [p for p in prices if p > 0]

def apply_tax(prices):
    """每个价格加上服务费。"""
    return [p * TAX_RATE for p in prices]

def average(values):
    """平均值，空列表返回 0。"""
    return sum(values) / len(values) if values else 0

def member_price(prices):
    """主函数：过滤 -> 加价 -> 均价 -> 会员折扣。"""
    taxed_avg = average(apply_tax(filter_valid(prices)))
    return taxed_avg * MEMBER_DISCOUNT

print(f"拆函数后输出：{member_price(data):.2f}")  # 三次输出必须一致

# 案例五：验证重构 —— 行为不变的证据
# 逐段对比中间值，确认每步等价
valid = filter_valid(data)
print(f"过滤后：{valid}")
taxed = apply_tax(valid)
print(f"加价后：{taxed}")
print(f"均价：{average(taxed):.2f}，会员价：{member_price(data):.2f}")
assert abs(b(data) - member_price(data)) < 1e-9, "重构前后结果不一致！"
print("重构验证通过：新旧实现输出一致")

# ===== 练习题 =====
# 1. 重构这段代码：def f(l): s=0\n for x in l:\n  if x%2==0: s+=x\n return s —— 改命名、换推导式，验证结果不变。
# 2. 把"输入成绩列表 -> 统计及格数 -> 打印及格率"的 10 行大函数拆成 3 个小函数，并输出相同结果。
# 3. 综合重构：对含魔法数字（0.85、100）的会员折扣代码做"提常量 + 拆函数 + assert 验证"三步改造，保持输出一致。
