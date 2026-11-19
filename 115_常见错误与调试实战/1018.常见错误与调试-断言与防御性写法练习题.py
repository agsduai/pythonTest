# ===== 第1018课：常见错误与调试-断言与防御性写法 =====
# 知识点：
#   - assert 条件, 提示：条件不成立就抛 AssertionError，用于"必须成立"的检查
#   - 防御性写法：先检查输入再干活，不让错误数据流进核心逻辑
#   - 区分两类错误：assert 用于开发期自查，if+raise 用于运行期拦截
#   - 早失败（fail fast）：错误出现得越早，排查成本越低

# 案例一：assert 检查折扣范围 —— 开发期自查
def apply_discount(price, discount):
    assert 0 < discount <= 1, f"折扣必须是 (0,1]，收到了 {discount}"
    return price * discount

print(f"9 折价：{apply_discount(100, 0.9)} 元")
try:
    apply_discount(100, 1.5)  # 折扣 1.5 显然是写错了
except AssertionError as e:
    print(f"断言拦住了错误参数：{e}")

# 案例二：防御性写法 —— 先验证再计算
# 场景：外卖平台计算配送费
def delivery_fee(distance_km):
    if distance_km <= 0:
        raise ValueError(f"距离必须是正数，收到了 {distance_km}")
    if distance_km > 10:
        raise ValueError("超出配送范围（10 公里）")
    return 5 + (distance_km - 1) * 1.5 if distance_km > 1 else 5

for d in [3, -1, 12]:
    try:
        print(f"{d} 公里配送费：{delivery_fee(d)} 元")
    except ValueError as e:
        print(f"拒绝订单：{e}")

# 案例三：早失败 —— 入口处拦截脏数据
# 场景：批量导入学生成绩，先整体检查再处理
raw_scores = [88, 92, 105, 75]  # 105 超过了满分
def validate(scores):
    for i, s in enumerate(scores):
        if not 0 <= s <= 100:
            raise ValueError(f"第 {i} 个成绩 {s} 不在 0~100 范围")
    return True

try:
    validate(raw_scores)
    print("校验通过，开始统计平均分")
except ValueError as e:
    print(f"导入中止：{e}")  # 有一处脏数据就整体拦截，避免半套脏数据入库

# 案例四：assert 的注意点 —— 别用它处理业务校验
# python -O 运行时 assert 会被整体跳过，所以业务校验要用 if + raise
def withdraw(balance, amount):
    if amount <= 0:
        raise ValueError("取款金额必须为正")  # 业务规则用异常，不用 assert
    return balance - amount

try:
    withdraw(100, -50)
except ValueError as e:
    print(f"银行拒绝交易：{e}")

# ===== 练习题 =====
# 1. 写函数 set_age(age)：assert 保证 1~120 之间，否则报 AssertionError 并带上提示，用 25 和 300 测试。
# 2. 写函数 divide(a, b)：防御式检查 b 为 0 时抛 ZeroDivisionError("除数不能为 0")，用 10/2 和 10/0 测试。
# 3. 成绩列表 [90, 85, -1, 77]，写校验函数整体拦截非法数据；通过后打印平均分，不通过打印"数据非法"。
