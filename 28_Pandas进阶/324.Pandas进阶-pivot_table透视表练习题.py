# ===== 第324课：Pandas进阶-pivot_table透视表 =====
# 知识点：
#   - 透视表：长表 → 交叉汇总表，Excel 透视图的编程版
#   - index=行分组 / columns=列分组 / values=统计值 / aggfunc=聚合方式
#   - fill_value 填空、margins=True 加合计行列
#   - 与 groupby+unstack 等价，透视表语法更直观
# 依赖：pip install pandas

import pandas as pd

df = pd.DataFrame({
    "日期": ["11-01", "11-01", "11-02", "11-02", "11-03", "11-03"],
    "地区": ["北京", "上海", "北京", "上海", "北京", "上海"],
    "品类": ["键盘", "键盘", "鼠标", "显示器", "鼠标", "键盘"],
    "金额": [796, 398, 199, 1299, 249, 500],
})
print(df, end="\n\n")

# 行=地区，列=品类，值=金额求和
pt = pd.pivot_table(
    df, index="地区", columns="品类", values="金额",
    aggfunc="sum", fill_value=0, margins=True, margins_name="合计",
)
print(pt, end="\n\n")

# 等价的 groupby 写法（对照理解）
print(df.groupby(["地区", "品类"])["金额"].sum().unstack(fill_value=0), end="\n\n")

# 换聚合方式：每格订单数；换成均值
print("订单数透视：", pd.pivot_table(df, index="地区", columns="品类",
      values="金额", aggfunc="count", fill_value=0), sep="\n")
print("平均客单价：", pd.pivot_table(df, index="地区", values="金额", aggfunc="mean"), sep="\n")

# ===== 练习题 =====
# 1. 行=品类、列=日期，统计每天各品类的销售额。
# 2. 用 margins 看每个地区的总销售额，找出最高的地区。
# 3. 思考：什么时候 groupby 更顺手，什么时候透视表更清楚？
