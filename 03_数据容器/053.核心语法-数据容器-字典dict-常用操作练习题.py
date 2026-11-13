# ===== 第053课：核心语法-数据容器-字典dict-常用操作 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 新增 / 修改：字典[键] = 值
#   - 删除：pop(键)、del 字典[键]、clear()
#   - 查询：get()、keys()、values()、items()
#   - 遍历字典的三种方式
#   - 成员判断 in、长度 len()

# ---------- 示例代码 ----------
student = {"name": "小明", "age": 18}

# 1. 新增与修改
student["score"] = 95              # 键不存在，新增
student["age"] = 19                # 键存在，修改
print(student)

# 2. 批量更新：update() 用另一个字典更新当前字典
student.update({"city": "北京", "score": 96})
print(student)

# 3. 删除
city = student.pop("city")         # 删除并返回被删除的值
print("删除的city：", city)
del student["score"]               # 用 del 删除指定键
print(student)

# 4. 查询键、值、键值对
print(student.keys())              # 所有键
print(student.values())            # 所有值
print(student.items())             # 所有键值对

# 5. 遍历字典
for key in student:
    print(key, student[key])

for value in student.values():
    print(value)

for key, value in student.items():
    print(key, "=", value)

# 6. 成员判断、清空
print("name" in student)
student.clear()
print("清空后：", student, len(student))

# ===== 练习题 =====
# 1. 字典 goods = {"苹果": 5, "香蕉": 3}，把苹果的数量改为 8，新增 "橙子": 6，用 pop() 删除香蕉并打印被删除的数量。
# 2. 遍历 goods 的所有键值对，打印“水果名：数量”的格式。
# 3. 字典 scores = {"语文": 90, "数学": 88, "英语": 92}，遍历所有值求总分和平均分并打印。
