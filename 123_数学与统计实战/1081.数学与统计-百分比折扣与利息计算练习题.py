# ===== 第1081课：数学与统计-百分比折扣与利息计算 =====
# 知识点：
#   - 折扣：原价 * 折扣率；"打 8 折" = * 0.8
#   - 百分比：小数与百分数互换（0.25 <-> 25%）；增长/下降率 = (新-旧)/旧
#   - 单利：本金 * 利率 * 年数；复利：本金 * (1+利率) ** 年数
#   - 浮点会带长尾巴，展示时统一 round 或 :.2f

# 案例一：折扣与满减对比
# 场景：打 7 折 vs 满 100 减 35，哪个划算
price = 150
discount_price = price * 0.7
reduction_price = price - 35 if price >= 100 else price
print(f"打 7 折：{discount_price:.2f} 元，满减：{reduction_price:.2f} 元")
print(f"更便宜的是：{'打折' if discount_price < reduction_price else '满减'}")

# 案例二：涨跌幅计算
# 场景：商品从 80 涨到 92，涨幅多少
old, new = 80, 92
change_rate = (new - old) / old
print(f"涨幅：{change_rate:.1%}")  # 15.0%（:1% 自动乘 100）
drop = 92 * (1 - 0.15)  # 涨 15% 后再降 15% 并不回到原价
print(f"涨 15% 后再降 15%：{drop:.2f} 元（比原价 80 低，涨跌幅度相同但基准变了）")

# 案例三：单利与复利
# 场景：1 万元存 3 年，年利率 3%
principal, rate, years = 10000, 0.03, 3
simple = principal * (1 + rate * years)
compound = principal * (1 + rate) ** years
print(f"单利本息：{simple:.2f} 元")
print(f"复利本息：{compound:.2f} 元（利滚利多赚 {compound - simple:.2f}）")

# 案例四：逐年展示复利增长
# 场景：每年年末余额
balance = principal
for year in range(1, years + 1):
    balance *= (1 + rate)
    print(f"第 {year} 年末：{balance:.2f} 元")

# 案例五：反推原价
# 场景：折后价 84 元是打 7 折，原价多少
final_price, discount_rate = 84, 0.7
original = final_price / discount_rate
print(f"原价：{original:.2f} 元（{original:.0f} = 84 / 0.7）")

# ===== 练习题 =====
# 1. 商品原价 299，先打 8 折再用满 200 减 30 券，打印最终价格与总折扣率（:1% 格式）。
# 2. 写函数 compound_value(principal, rate, years)：返回复利本息，10000 元、5%、10 年应约 16288.95。
# 3. 计算奶茶店销量从 120 杯变为 95 杯的下降率，并反推要涨回原销量需要增长多少（验证不是同一个百分数）。
