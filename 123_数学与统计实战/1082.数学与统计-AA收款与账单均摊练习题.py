# ===== 第1082课：数学与统计-AA收款与账单均摊 =====
# 知识点：
#   - 均摊：总额 / 人数，除不尽时要处理"零头"（谁多付 1 分钱）
#   - 金额用"分"计算再转"元"，避免浮点误差（int 分 + divmod）
#   - divmod(a, b) 同时得到商和余数：商是每人基础份额，余数轮流补
#   - 实际场景：聚餐 AA、团购凑单、房租水电分摊

# 案例一：简单均摊
total, people = 300, 4
per = total / people
print(f"每人：{per:.2f} 元")

# 案例二：除不尽的 AA —— 按"分"算
# 场景：100 元 3 人分，每人 33.33，剩 1 分钱给第一个人
total_cents = 10000  # 100 元 = 10000 分
n = 3
base, remainder = divmod(total_cents, n)
print(f"每人基础：{base / 100:.2f} 元，剩余：{remainder} 分")
shares = [base + 1 if i < remainder else base for i in range(n)]
print(f"分摊结果：{[f'{s / 100:.2f}' for s in shares]} 元，合计 {sum(shares) / 100:.2f}")

# 案例三：带小数的账单 —— 先转分再分摊
# 场景：账单 267.35 元，4 人分
from decimal import Decimal

bill = Decimal("267.35")
per = bill / 4
print(f"精确每人：{per} 元，展示：{round(per, 2)} 元")

# 案例四：不同人不同份额 —— 按比例分摊
# 场景：打车 88 元，3 人按乘坐距离比例分（2:3:5）
fee = 88
weights = [2, 3, 5]
total_weight = sum(weights)
shares = [round(fee * w / total_weight, 2) for w in weights]
print(f"按比例分摊：{shares} 元，合计 {round(sum(shares), 2)} 元")

# 案例五：水电费按人头 + 公摊
# 场景：电费 180 元，其中 60 元公摊均分，其余按各屋用电度数分
total_fee, common_fee = 180, 60
private_fee = total_fee - common_fee
tenants = [("101", 120), ("102", 80), ("103", 100)]  # 各屋用电度数
total_kwh = sum(k for _, k in tenants)
common_part = common_fee / len(tenants)
for room, kwh in tenants:
    own = private_fee * kwh / total_kwh
    print(f"{room}：公摊 {common_part:.2f} + 自用电费 {own:.2f} = {common_part + own:.2f} 元")

# ===== 练习题 =====
# 1. 87 元 4 人 AA，用"分"计算实现零头分配，打印每人金额并验证合计等于 87。
# 2. 写函数 split_bill(amount, n)：返回每人应付列表（元，两位小数，余数给前面的人），用 (100, 3) 测试结果 [33.34, 33.33, 33.33]。
# 3. 三人拼单 156 元，出资比例 1:1:2，打印每人应付金额并检查合计与原额的差额（本题恰好整除；想看到 0.01 的舍入差额，可试试 10 元按 1:1:1 分）。
