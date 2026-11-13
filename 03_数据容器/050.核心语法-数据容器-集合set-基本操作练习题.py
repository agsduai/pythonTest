# ===== 第050课：核心语法-数据容器-集合set-基本操作 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 集合用 {} 定义，元素无序、不重复
#   - 空集合必须用 set()，{} 表示空字典
#   - 常用方法：add()、remove()、discard()、pop()、clear()
#   - 成员判断 in、长度 len()
#   - 集合运算：并集 |、交集 &、差集 -、对称差集 ^

# ---------- 示例代码 ----------
# 1. 定义集合：重复元素会自动去掉
numbers = {1, 2, 3, 2, 1}
print(numbers)                     # {1, 2, 3}，顺序不固定

# 2. 空集合要用 set()，不能用 {}
empty_set = set()
print(empty_set, len(empty_set))

# 3. 添加和删除元素
numbers.add(4)                     # 添加元素 4
numbers.add(2)                     # 已存在，集合不变
print("添加后：", numbers)
numbers.remove(2)                  # 删除元素，不存在会报错
numbers.discard(99)                # 删除元素，不存在也不报错
print("删除后：", numbers)

# 4. 成员判断与长度
print(3 in numbers)
print(len(numbers))

# 5. 集合运算
a = {1, 2, 3, 4}
b = {3, 4, 5, 6}
print("并集：", a | b)
print("交集：", a & b)
print("差集（a 有 b 没有）：", a - b)
print("对称差集（只在一个集合中）：", a ^ b)
print("a 是 b 的子集吗：", a <= b)

# 6. 遍历集合（顺序不固定）
for item in a:
    print(item)

# ===== 练习题 =====
# 1. 定义集合 s = {10, 20, 20, 30}，打印集合，并输出集合的长度。
# 2. 向集合 s 中添加 40，删除 20（用 discard），再判断 30 是否在集合中。
# 3. 定义集合 x = {1, 2, 3, 4}、y = {3, 4, 5}，分别求并集、交集、差集 x - y、对称差集。
