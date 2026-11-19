# ===== 第1013课：常见错误与调试-IndexError与越界排查 =====
# 知识点：
#   - IndexError：下标超出范围，比如列表只有 3 个元素却取 [3]
#   - len() 是防越界的第一工具：先量长度再取下标
#   - 正向下标从 0 开始，最后一个元素下标是 len-1
#   - 遍历时不要一边删元素一边用原下标，最容易越界

# 案例一：购物清单越界 —— 取不存在的下标
goods = ["牛奶", "面包", "鸡蛋"]
# print(goods[3])  # 报 IndexError: list index out of range
# 解读：列表只有 3 个元素，合法下标是 0、1、2，没有 3
print(f"最后一个商品：{goods[len(goods) - 1]}")  # 先量长度再取，稳
print(f"最后一个商品（更简单）：{goods[-1]}")  # -1 就是最后一项

# 案例二：空列表取值 —— 新手最常见的崩溃
cart = []  # 购物车可能是空的
if len(cart) > 0:
    print(f"购物车第一件：{cart[0]}")
else:
    print("购物车是空的，不能直接取 cart[0]")  # 空列表取任何下标都会越界

# 案例三：循环中边删边遍历导致漏项或越界
# 场景：清空购物车里所有"过期"商品
foods = [("牛奶", True), ("面包", False), ("酸奶", True)]
# 错误写法：一边 for 一边 remove，元素位置会移动，结果漏删
# 正确做法：先收集要删的，再统一删
expired = [f for f in foods if f[1]]
for item in expired:
    foods.remove(item)
print(f"清理后购物车：{foods}")

# 案例四：用 range(len()) 或 enumerate 遍历，避免手动算下标
seats = ["A1", "A2", "A3"]
for i in range(len(seats)):
    print(f"座位号 {i}：{seats[i]}")
# 更推荐 enumerate，下标和元素一起给，不会算错
for i, seat in enumerate(seats):
    print(f"第 {i + 1} 个座位：{seat}")

# ===== 练习题 =====
# 1. 定义列表 scores = [88, 92, 75]，分别打印第一个、最后一个元素；再把列表清空后尝试安全地取第一个元素（不报错）。
# 2. 写函数 get_item(lst, idx)：下标合法返回对应元素，不合法返回 None 并打印"下标越界"。
# 3. 列表 orders = ["A", "B", "C", "D"]，要求删除所有 "C" 和 "A"：先写一段边遍历边 remove 的代码观察漏删现象，再写正确做法。
