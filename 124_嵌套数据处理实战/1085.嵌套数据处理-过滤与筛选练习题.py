# ===== 第1085课：嵌套数据处理-过滤与筛选 =====
# 知识点：
#   - 过滤列表套字典：[x for x in 数据 if 条件]，条件可组合多个字段
#   - 推导式里还能"同时改字段"：过滤 + 投影一步完成
#   - any/all 配生成器：判断"有没有/是不是全都"满足
#   - 实际场景：筛选未支付订单、找 VIP 大客户、筛库存告急商品

# 案例一：单条件过滤
orders = [
    {"id": "O1", "amount": 120, "status": "paid"},
    {"id": "O2", "amount": 45, "status": "pending"},
    {"id": "O3", "amount": 200, "status": "paid"},
    {"id": "O4", "amount": 80, "status": "pending"},
]
pending = [o for o in orders if o["status"] == "pending"]
print(f"待支付订单：{[o['id'] for o in pending]}")

# 案例二：多条件组合
# 场景：已支付且金额 >= 100 的"大单"
big_paid = [o["id"] for o in orders if o["status"] == "paid" and o["amount"] >= 100]
print(f"已支付大单：{big_paid}")  # O1、O3

# 案例三：过滤 + 投影 —— 只挑出需要的字段
# 场景：给客服看简化视图（只要 id 和金额）
simple_view = [{"id": o["id"], "amount": o["amount"]} for o in orders]
print(f"简化视图：{simple_view[:2]}")  # 打印前两条看看

# 案例四：any / all 快速判断
# 场景：是否有待支付订单？是否全部已支付？
print(f"有未支付订单：{any(o['status'] == 'pending' for o in orders)}")
print(f"全部已支付：{all(o['status'] == 'paid' for o in orders)}")

# 案例五：嵌套两层过滤 —— 订单里再筛商品
# 场景：找出"包含牛奶"的订单
orders_with_items = [
    {"id": "A1", "items": ["苹果", "牛奶"]},
    {"id": "A2", "items": ["面包"]},
    {"id": "A3", "items": ["牛奶", "酸奶"]},
]
milk_orders = [o["id"] for o in orders_with_items if "牛奶" in o["items"]]
print(f"含牛奶的订单：{milk_orders}")

# 反向：排除含某商品
no_milk = [o["id"] for o in orders_with_items if "牛奶" not in o["items"]]
print(f"不含牛奶的订单：{no_milk}")

# ===== 练习题 =====
# 1. 从案例一 orders 中筛出金额在 50~150 之间的订单号列表，输出 ["O1", "O4"]。
# 2. 用户列表含 age 和 vip 字段，筛出 vip 为 True 且年龄 >= 20 的人的姓名列表。
# 3. 写函数 find_low_stock(products, threshold)：products 是列表套字典（含 name/stock），返回库存低于阈值的商品名，用 3 条数据测试。
