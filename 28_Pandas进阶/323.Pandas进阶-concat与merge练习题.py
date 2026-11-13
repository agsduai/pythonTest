# ===== 第323课：Pandas进阶-concat与merge =====
# 知识点：
#   - pd.concat：按轴拼接（上下堆叠 / 左右并排）
#   - pd.merge：按键关联 —— 就是 SQL 的 JOIN（第301课）
#   - how 参数：inner 内连接（默认）/ left 左连接
#   - ignore_index=True：拼接后重建行号
# 依赖：pip install pandas

import pandas as pd

# ---- concat：结构相同的表上下摞 ----
df1 = pd.DataFrame({"姓名": ["小明", "小红"], "语文": [92, 85]})
df2 = pd.DataFrame({"姓名": ["小刚", "小丽"], "语文": [76, 88]})
print(pd.concat([df1, df2], ignore_index=True), end="\n\n")

# 标记来源：加一层 keys
print(pd.concat([df1, df2], keys=["一班", "二班"]), end="\n\n")

# ---- merge：按键关联 ----
orders = pd.DataFrame({
    "订单号": ["A1", "A2", "A3"],
    "用户": ["小明", "小红", "小明"],
    "金额": [99, 199, 59],
})
users = pd.DataFrame({"用户": ["小明", "小红"], "城市": ["北京", "上海"]})

print("inner join（默认）：", pd.merge(orders, users, on="用户"), sep="\n", end="\n\n")
print("left join（订单全保留）：", pd.merge(orders, users, on="用户", how="left"), sep="\n")

# ---- 反向：哪位用户没有任何订单 ----
all_users = pd.DataFrame({"用户": ["小明", "小红", "小刚"]})
no_order = pd.merge(all_users, orders, on="用户", how="left", indicator=True)
print("没下过单的用户：", no_order.loc[no_order["_merge"] == "left_only", "用户"].tolist())

# ===== 练习题 =====
# 1. 把三个班的成绩表 concat 成总表，并保留“班级”来源列。
# 2. 用 merge 统计每位用户的累计消费（merge + groupby）。
# 3. 思考：concat 与 merge 的适用条件各是什么？
