# ===== 第1022课：推导式与内置函数-字典推导式 =====
# 知识点：
#   - 字典推导式：{键表达式: 值表达式 for 变量 in 可迭代对象}
#   - 键或值都可以做运算、调函数，常用于"翻转字典"和"构建映射"
#   - 键重复时后面的会覆盖前面的，去重翻转时要注意
#   - 配合 zip() 可以把两个列表拼成字典

# 案例一：从商品列表构建"商品->价格"字典
# 场景：两个列表，一个是商品名，一个是价格
goods = ["苹果", "牛奶", "面包"]
prices = [5.5, 8.0, 12.0]
price_map = {g: p for g, p in zip(goods, prices)}
print(f"价格表：{price_map}")

# 案例二：字典翻转 —— 把 "学号->姓名" 变成 "姓名->学号"
students = {101: "小张", 102: "小李", 103: "小王"}
name_map = {name: sid for sid, name in students.items()}
print(f"翻转后：{name_map}")

# 案例三：值做运算 —— 给所有商品涨价 10%
old_map = {"苹果": 5.5, "牛奶": 8.0, "面包": 12.0}
new_map = {g: round(p * 1.1, 2) for g, p in old_map.items()}
print(f"涨价后：{new_map}")

# 案例四：带条件过滤 —— 只保留贵的商品
expensive = {g: p for g, p in old_map.items() if p >= 8}
print(f"8 元以上商品：{expensive}")

# 案例五：按首字母分组索引（键重复场景注意覆盖）
words = ["apple", "banana", "avocado", "blueberry"]
# 每个首字母只记最后一个词（覆盖），要全收集应该用 value 是列表
first_index = {w[0]: w for w in words}
print(f"首字母索引（覆盖）：{first_index}")  # {'a': 'avocado', 'b': 'blueberry'}
groups = {}
for w in words:
    groups.setdefault(w[0], []).append(w)  # 全收集用 setdefault + append
print(f"首字母分组：{groups}")

# ===== 练习题 =====
# 1. 有 keys = ["name", "age", "city"] 和 values = ["小张", 25, "深圳"]，用 zip + 字典推导式合成字典。
# 2. 把 {"a": 1, "b": 2, "c": 3} 用字典推导式翻转成 {1: "a", 2: "b", 3: "c"}。
# 3. 用字典推导式生成 {1: 1的平方, ..., 5: 5的平方}，即 {1: 1, 2: 4, 3: 9, 4: 16, 5: 25}。
