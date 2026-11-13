# ===== 第211课：测试与工程化-断言与调试基础 =====
# 知识点：
#   - assert 条件, 提示信息：条件不成立抛 AssertionError
#   - assert 表达“确认代码按预期工作”，是单元测试的原子操作
#   - 注意：python -O 运行会忽略 assert，正式的参数校验要用 if + raise
#   - 调试三板斧：print 观察法 → 断言/日志 → IDE 断点调试
#   - 先写小验证再放大功能：小步快跑减少调试成本


def divide(a, b):
    assert b != 0, "除数不能为 0"        # 前置条件检查（面向开发者）
    return a / b


print(divide(10, 2))          # 5.0

try:
    divide(10, 0)
except AssertionError as exc:
    print(f"断言拦截：{exc}")


# assert 是“期望”，不是“校验用户输入”：外部输入用 if + raise
def set_age(age):
    if not isinstance(age, int) or age < 0:
        raise ValueError(f"年龄必须是正整数，收到：{age}")
    return age


print(set_age(18))
try:
    set_age(-1)
except ValueError as exc:
    print(f"参数校验：{exc}")


# print 观察法：在关键节点打印中间值（需要时打开注释）
def sum_even(n):
    total = 0
    for i in range(n + 1):
        if i % 2 == 0:
            # print(f"调试：i={i}, total={total}")
            total += i
    return total


print(sum_even(10))     # 2+4+6+8+10 = 30


# 手写“迷你测试”：用 assert 组成简单的自测函数
def test_sum_even():
    assert sum_even(0) == 0
    assert sum_even(1) == 0
    assert sum_even(10) == 30
    assert sum_even(11) == 30
    print("test_sum_even 全部通过")


test_sum_even()

# ===== 练习题 =====
# 1. 给 divide 增加返回值断言：divide(9, 3) == 3.0。
# 2. 编写函数 is_palindrome(s)，并用 3 条 assert 验证回文判断。
# 3. 故意把 sum_even 改错（range(n)），观察测试如何帮你抓住问题。
# 4. 思考：assert 与 raise 各自适合的场景是什么？
