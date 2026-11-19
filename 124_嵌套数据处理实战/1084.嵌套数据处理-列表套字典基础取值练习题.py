# ===== 第1084课：嵌套数据处理-列表套字典基础取值 =====
# 知识点：
#   - 真实数据几乎都是"列表套字典"：[{...}, {...}, ...]，如订单列表、用户列表
#   - 取一条：data[0]["字段"]；遍历：for item in data 再 item["字段"]
#   - 找某一条：循环 + if 匹配，或用 next 找第一个
#   - 先弄清"数据的形状"：是列表套字典，还是字典套列表

# 案例一：认识数据的形状
users = [
    {"name": "小张", "age": 18, "city": "北京"},
    {"name": "小李", "age": 25, "city": "上海"},
    {"name": "小王", "age": 30, "city": "深圳"},
]
print(f"外层是列表：{len(users)} 个元素")
print(f"内层是字典：{list(users[0].keys())}")
print(f"第一个人的名字：{users[0]['name']}")

# 案例二：遍历提取字段
# 场景：打印所有人的姓名和城市
for u in users:
    print(f"{u['name']}（{u['city']}）")
# 推导式一次性提取
names = [u["name"] for u in users]
print(f"姓名列表：{names}")

# 案例三：查找某个人
# 场景：按姓名查找用户信息
target = "小李"
found = None
for u in users:
    if u["name"] == target:
        found = u
        break
print(f"查找 {target}：{found}")
# next 一行写法（找不到返回 None）
found2 = next((u for u in users if u["name"] == "小赵"), None)
print(f"查找不存在的人：{found2}")

# 案例四：字典里还套列表 —— 订单详情
# 场景：订单里有"商品明细"子列表
order = {
    "id": "A001",
    "customer": "小张",
    "items": [
        {"goods": "苹果", "qty": 3, "price": 5.5},
        {"goods": "牛奶", "qty": 2, "price": 8.0},
    ],
}
total = sum(i["qty"] * i["price"] for i in order["items"])
print(f"订单 {order['id']} 总价：{total:.2f} 元")
goods_names = [i["goods"] for i in order["items"]]
print(f"商品清单：{goods_names}")

# ===== 练习题 =====
# 1. 用案例一的 users：打印年龄最大的人的完整信息，和所有人的城市列表（去重）。
# 2. 写函数 find_user(users, name)：找到返回该字典，找不到返回 None，分别测"小李"和"小赵"。
# 3. 订单列表 orders 含 3 笔订单（各带 items），写循环打印每笔订单号与总价，并求全部订单总金额。
