# ===== 第1087课：嵌套数据处理-修改与更新 =====
# 知识点：
#   - 直接改：循环里 item["字段"] = 新值；增字段：item["新字段"] = 值
#   - 推导式是"造新列表"，修改要用循环或列表推导重建
#   - 批量更新前先想清楚"要不要动原数据"：可先 copy 再改
#   - 删除字段：del item["字段"] 或 item.pop("字段", None)

# 案例一：批量修改字段
# 场景：所有商品涨价 10%
products = [
    {"name": "苹果", "price": 5.5},
    {"name": "牛奶", "price": 8.0},
    {"name": "面包", "price": 12.0},
]
for p in products:
    p["price"] = round(p["price"] * 1.1, 2)
print(f"涨价后：{products}")

# 案例二：新增字段
# 场景：按价格打标"贵/便宜"
for p in products:
    p["level"] = "贵" if p["price"] >= 10 else "便宜"
print(f"打标后：{[(p['name'], p['level']) for p in products]}")

# 案例三：条件更新 —— 只改满足条件的
# 场景：只有库存少于 10 的才补货到 20
inventory = [
    {"name": "苹果", "stock": 5},
    {"name": "牛奶", "stock": 30},
    {"name": "面包", "stock": 8},
]
for item in inventory:
    if item["stock"] < 10:
        item["stock"] = 20
        print(f"补货：{item['name']} -> 20")
print(f"补货后库存：{[(i['name'], i['stock']) for i in inventory]}")

# 案例四：保留原数据的修改 —— 先复制再改
# 场景：生成"促销价"列表但不影响原价
original = [{"name": "苹果", "price": 5.5}, {"name": "牛奶", "price": 8.0}]
promo = [{**item, "price": round(item["price"] * 0.8, 2)} for item in original]
# {**item, ...} 是"复制字典并追加/覆盖字段"的简写
print(f"原价：{original}")
print(f"促销价：{promo}")

# 案例五：删除字段
# 场景：对外输出时隐藏内部字段
internal = [{"name": "小张", "age": 18, "salary": 8000}, {"name": "小李", "age": 25, "salary": 9000}]
public = []
for item in internal:
    cleaned = {k: v for k, v in item.items() if k != "salary"}  # 推导式重建并排除
    public.append(cleaned)
print(f"对外数据：{public}")

# ===== 练习题 =====
# 1. 给案例一 products 每项增加 "vip_price" 字段 = price * 0.9（round 两位），打印商品名与 VIP 价。
# 2. 订单列表中把 status 从 "pending" 改为 "paid"（只改金额 >= 100 的），打印修改前后各订单状态。
# 3. 写函数 normalize(items, fields)：返回只保留 fields 列表里字段的新列表，用 ["name", "price"] 测试案例一数据。
