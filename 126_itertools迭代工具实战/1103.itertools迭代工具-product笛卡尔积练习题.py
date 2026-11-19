# ===== 第1103课：itertools迭代工具-product笛卡尔积 =====
# 知识点：
#   - product(A, B)：所有搭配两两组合，A 的每个元素配 B 的每个元素
#   - 组合数 = len(A) * len(B)，2 主食 x 3 饮料 = 6 种套餐
#   - repeat 参数：product(序列, repeat=2) 是"自己和自己配"（如坐标格）
#   - 实际场景：套餐搭配、测试参数组合、生成棋盘坐标

# 案例一：套餐搭配
import itertools

staples = ["米饭", "面条"]
drinks = ["可乐", "果汁", "酸奶"]
combos = list(itertools.product(staples, drinks))
print(f"共 {len(combos)} 种套餐：")
for staple, drink in combos:
    print(f"  {staple} + {drink}")

# 案例二：三种选择一起配 —— 密码穷举思路
# 场景：2 位二进制一共几种
bits = list(itertools.product("01", "01"))
print(f"2 位二进制：{'、'.join(''.join(b) for b in bits)}")  # 4 种

# 用 repeat 更简洁
bits2 = ["".join(b) for b in itertools.product("01", repeat=3)]
print(f"3 位二进制（repeat=3）：{bits2}")  # 8 种

# 案例三：棋盘坐标
# 场景：3x3 九宫格的所有坐标
cells = list(itertools.product(range(3), repeat=2))
print(f"九宫格坐标：{cells}")

# 案例四：测试参数组合 —— 单元测试好用
# 场景：用户类型 x 支付方式，每种都要测一遍
user_types = ["游客", "会员"]
pay_types = ["微信", "支付宝"]
test_cases = list(itertools.product(user_types, pay_types))
print(f"测试矩阵（{len(test_cases)} 组）：")
for u, p in test_cases:
    print(f"  测试：{u} 用 {p} 支付")

# 案例五：搭配带价格 —— 算每种套餐总价
menu = {"米饭": 3, "面条": 5}
drink_price = {"可乐": 3, "果汁": 5, "酸奶": 4}
for staple, drink in combos:
    print(f"{staple}+{drink} 套餐价：{menu[staple] + drink_price[drink]} 元")

# ===== 练习题 =====
# 1. 用 product 列出 3 件上衣 x 2 条裤子的全部穿搭，输出总数与列表。
# 2. 用 product(range(2), repeat=3) 生成所有三维坐标点并打印数量（应为 8）。
# 3. 写函数 make_combos(*option_groups)：接受任意多个选项组返回全部搭配，用 (["大","小"], ["红","蓝"], ["杯装","盒装"]) 测试，验证总数是 2*2*2=8。
