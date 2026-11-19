# ===== 第1086课：嵌套数据处理-排序与TopN =====
# 知识点：
#   - 按字段排序：sorted(数据, key=lambda x: x["字段"])
#   - 降序加 reverse=True；TopN 用切片 [:n]
#   - 多字段排序：key 返回元组 (第一条件, 第二条件)
#   - max/min 也能带 key：直接拿"整个字典"而不只是值

# 案例一：按金额排序
orders = [
    {"id": "O1", "amount": 120},
    {"id": "O2", "amount": 45},
    {"id": "O3", "amount": 200},
    {"id": "O4", "amount": 80},
]
by_amount = sorted(orders, key=lambda o: o["amount"])
print(f"升序：{[o['id'] for o in by_amount]}")
by_amount_desc = sorted(orders, key=lambda o: o["amount"], reverse=True)
print(f"降序：{[o['id'] for o in by_amount_desc]}")

# 案例二：TopN —— 销量前三
# 场景：商品销量排行榜
products = [
    {"name": "苹果", "sold": 30},
    {"name": "牛奶", "sold": 45},
    {"name": "面包", "sold": 25},
    {"name": "酸奶", "sold": 50},
    {"name": "鸡蛋", "sold": 40},
]
top3 = sorted(products, key=lambda p: p["sold"], reverse=True)[:3]
for rank, p in enumerate(top3, start=1):
    print(f"第 {rank} 名：{p['name']}（{p['sold']} 件）")

# 案例三：多字段排序 —— 先班级后分数
# 场景：同班级内按分数从高到低
students = [
    {"cls": "二班", "name": "小赵", "score": 88},
    {"cls": "一班", "name": "小张", "score": 90},
    {"cls": "二班", "name": "小李", "score": 95},
    {"cls": "一班", "name": "小王", "score": 78},
]
sorted_students = sorted(students, key=lambda s: (s["cls"], -s["score"]))
for s in sorted_students:
    print(f"{s['cls']} {s['name']}：{s['score']}")

# 案例四：max/min 直接拿整个字典
best = max(products, key=lambda p: p["sold"])
worst = min(products, key=lambda p: p["sold"])
print(f"销量王：{best['name']}，垫底：{worst['name']}")

# 案例五：排序 + 投影组合
# 场景：按分数排序后只输出 "姓名 分数" 文本
report = sorted(students, key=lambda s: -s["score"])
lines = [f"{s['name']} {s['score']} 分" for s in report]
print(f"成绩单：{lines}")

# ===== 练习题 =====
# 1. 把案例一 orders 按"金额降序"打印订单号，再打印总金额前两名的订单号（Top2）。
# 2. 员工列表含 name/salary/dept：按部门升序、部门内工资降序排序，打印完整报表。
# 3. 写函数 top_n(items, key_field, n)：通用 TopN 函数，返回按 key_field 降序的前 n 个字典，用销量数据测试 n=2。
