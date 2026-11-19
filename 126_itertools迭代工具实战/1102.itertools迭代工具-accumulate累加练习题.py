# ===== 第1102课：itertools迭代工具-accumulate累加 =====
# 知识点：
#   - accumulate(序列)：逐步累加，返回"每一步的累计值"
#   - 第二参数可换运算：accumulate(序列, max) 得到"到目前为止的最大值"
#   - 用 list() 展开看全部；惰性求值可直接循环
#   - 实际场景：账单累计、月度销售累计曲线、连续最高纪录

# 案例一：基础累加
import itertools

bills = [30, 12, 45, 8]
running_total = list(itertools.accumulate(bills))
print(f"每笔账单：{bills}")
print(f"累计金额：{running_total}")  # 30, 42, 87, 95

# 案例二：累计销售曲线
# 场景：1~6 月各月销售额与累计销售额
monthly = [120, 90, 150, 80, 200, 130]
cum = list(itertools.accumulate(monthly))
for month, (m, c) in enumerate(zip(monthly, cum), start=1):
    print(f"{month} 月：当月 {m}，累计 {c}")

# 案例三：自定义运算 —— 累计最大值
# accumulate(数据, max)：到当前位置为止见过的最大值
daily_prices = [10, 12, 11, 15, 13, 18]
high_water = list(itertools.accumulate(daily_prices, max))
print(f"每日最高纪录：{high_water}")  # 只会上升

# 案例四：自定义函数的累加
# 场景：账户余额流水（上一笔 + 本笔变动，可为负）
def add_balance(prev, change):
    return prev + change

changes = [1000, -200, -300, 500]
balance_flow = list(itertools.accumulate(changes, add_balance, initial=0))
# initial 是"起点值"（Python 3.8+）
print(f"余额流水：{balance_flow}")

# 案例五：progress 百分比进度
# 场景：下载进度按已下载字节数算百分比
chunks = [20, 30, 10, 40]  # 每段 MB
totals = list(itertools.accumulate(chunks))
overall = totals[-1]
for i, t in enumerate(totals, start=1):
    print(f"段 {i} 完成后：{t / overall:.0%}")

# ===== 练习题 =====
# 1. 用 accumulate 计算存款 [500, 200, -100, 300] 的累计余额并打印。
# 2. 用 accumulate + max 找出跑步记录 [5, 8, 6, 10, 9, 12]（公里）的"历史最长里程曲线"。
# 3. 写函数 grade_scale(scores, total)：用 accumulate 算每科累计分占比，输入 [90, 80, 85]，total=300，输出每步百分数。
