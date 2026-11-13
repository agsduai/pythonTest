# ===== 第330课：Pandas进阶-综合案例-电商订单分析 =====
# 知识点：
#   - 综合运用：merge（323）+ 透视表（324）+ 分箱（328）+ 时间序列（327）
#   - 场景：1000 笔订单 + 用户表 → 一份完整经营分析
#   - 产出 Excel 多 sheet 报表（第290/329课）
# 依赖：pip install pandas numpy openpyxl

import os

import numpy as np
import pandas as pd

# ---- 1. 模拟数据：30 天、1000 笔订单 ----
rng = np.random.default_rng(7)
cities = pd.DataFrame({
    "用户": [f"用户{i}" for i in range(50)],
    "城市": rng.choice(["北京", "上海", "广州"], size=50),
})
orders = pd.DataFrame({
    "订单号": [f"O{i:04d}" for i in range(1000)],
    "用户": rng.choice(cities["用户"], size=1000),
    "品类": rng.choice(["数码", "服饰", "食品", "图书"], size=1000, p=[0.3, 0.25, 0.3, 0.15]),
    "金额": rng.integers(20, 2000, size=1000),
    "日期": pd.date_range("2026-10-15", periods=1000, freq="h").normalize()[:1000],
})

# ---- 2. 关联用户信息（merge）----
data = orders.merge(cities, on="用户")

# ---- 3. 分析一：品类 GMV 与城市分布 ----
gmv = data.pivot_table(index="品类", columns="城市", values="金额", aggfunc="sum", fill_value=0, margins=True)
print("品类×城市 GMV：", gmv, sep="\n")

# ---- 4. 分析二：客单价分箱（cut）----
data["档位"] = pd.cut(data["金额"], bins=[0, 200, 1000, 2000], labels=["小额", "中额", "大额"])
print("档位分布：", data["档位"].value_counts().to_dict())

# ---- 5. 分析三：周度趋势（resample）----
data = data.set_index("日期")
weekly = data.resample("W")["金额"].sum()
print("周度GMV：", weekly.round(0).to_dict(), sep="\n")

# ---- 6. 分析四：Top10 用户 ----
top10 = data.groupby(["用户", "城市"])["金额"].sum().sort_values(ascending=False).head(10).reset_index()
print("Top10 用户：", top10.to_dict("records")[:3], "...", sep="\n")

# ---- 7. 导出多 sheet 报表 ----
with pd.ExcelWriter("ecom_report_330.xlsx") as writer:
    gmv.to_excel(writer, sheet_name="品类城市GMV")
    data["档位"].value_counts().to_frame("订单数").to_excel(writer, sheet_name="档位分布")
    weekly.to_frame("周GMV").to_excel(writer, sheet_name="周度趋势")
    top10.to_excel(writer, sheet_name="Top10用户", index=False)
    sheet_names = writer.book.sheetnames      # 关闭前取名字，避免句柄未释放删不了文件
print("报表已导出：ecom_report_330.xlsx，", sheet_names)

os.remove("ecom_report_330.xlsx")

# ===== 练习题 =====
# 1. 计算复购用户占比：下过 ≥2 单的用户数 / 总用户数。
# 2. 给周度趋势加上“环比增长率”。
# 3. 思考：如果订单表有 1 亿行，这份代码哪些步骤要换成数据库聚合（第25章）？
