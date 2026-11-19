# ===== 第1017课：常见错误与调试-print调试法 =====
# 知识点：
#   - print 调试法：在关键位置打印变量值，看程序"走到哪、值变成什么"
#   - 打印三要素：位置标记 + 变量名 + 变量值，一眼定位问题
#   - f"{变量=}" 可以一次打印变量名和值（Python 3.8+）
#   - 调试完记得删掉或注释调试 print，别留在正式代码里

# 案例一：定位计算错误 —— 打印每一步的中间值
# 场景：订单优惠后金额不对，逐步打印找原因
price = 100
discount = 0.8
count = 3
step1 = price * discount
print(f"[调试] step1 单价打折 = {step1}")  # 80.0
step2 = step1 * count
print(f"[调试] step2 乘数量 = {step2}")  # 240.0
# 发现：漏了满减 20 元，继续往下修
final = step2 - 20
print(f"最终金额：{final}")

# 案例二：循环里打印 —— 看每轮的值怎么变
# 场景：统计购物车总价，结果不对
cart = [("牛奶", 5), ("面包", 8), ("鸡蛋", 12)]
total = 0
for name, p in cart:
    total += p
    print(f"[调试] 加入 {name}（{p} 元），当前 total = {total}")
print(f"购物车总价：{total} 元")

# 案例三：变量名+值一起打印 —— f"{x=}" 语法
name = "小张"
level = "VIP"
balance = 66.5
print(f"[调试] {name=} {level=} {balance=}")
# 输出：[调试] name='小张' level='VIP' balance=66.5

# 案例四：函数进出的探针 —— 确认函数有没有被调用、参数是什么
def check_password(pwd):
    print(f"[调试] check_password 被调用，pwd 长度 = {len(pwd)}")  # 别打印密码本身
    if len(pwd) >= 8:
        return True
    print("[调试] 长度不足 8，直接返回 False")
    return False

print(f"校验结果：{check_password('12345')}")
print(f"校验结果：{check_password('12345678')}")

# ===== 练习题 =====
# 1. 写一段计算 1 到 10 累加的程序，在循环里用调试 print 打印每轮 i 和当前累加值，最后输出总和 55。
# 2. 有 buggy 代码 total = 100 / 3 * 3，结果不是 100，用 print 打印中间值解释为什么（提示：浮点精度）。
# 3. 写函数 is_vip(score)（>=100 是 VIP），故意先写错判断为 >100，用 f"{score=}" 调试找出错误并修正。
