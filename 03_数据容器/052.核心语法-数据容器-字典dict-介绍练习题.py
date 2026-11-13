# ===== 第052课：核心语法-数据容器-字典dict-介绍 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 字典用 {键: 值} 定义，保存“键值对”数据
#   - 键必须是不可变类型且唯一，值可以是任意类型
#   - 通过键取值：字典[键]，键不存在会报错
#   - get(键, 默认值) 取值更安全
#   - 字典可以嵌套，用来表示复杂数据

# ---------- 示例代码 ----------
# 1. 定义字典：姓名、年龄、成绩
student = {"name": "小明", "age": 18, "score": 95}
print(student)

# 2. 通过键取值
print(student["name"])             # 小明
print(student["score"])            # 95

# 3. 键不存在时，[] 会报错，get() 可以返回默认值
print(student.get("gender", "未知"))  # 未知
print(student.get("age", 0))          # 18

# 4. 修改已有键的值、添加新的键值对
student["score"] = 98              # 修改
student["gender"] = "男"           # 新增
print(student)

# 5. 判断键是否存在、字典长度
print("name" in student)
print("city" in student)
print("键值对个数：", len(student))

# 6. 嵌套字典：学生信息中再保存各科成绩
student2 = {
    "name": "小红",
    "age": 17,
    "scores": {"语文": 90, "数学": 88, "英语": 92}
}
print(student2["scores"]["数学"])   # 88

# ===== 练习题 =====
# 1. 定义字典 book = {"title": "Python入门", "price": 59, "author": "张三"}，打印书名和价格。
# 2. 用 get() 获取 book 中不存在的键 "publisher"，默认值设为 "未知出版社"；再给 book 添加键 "publisher"，值为 "人民邮电出版社"。
# 3. 定义嵌套字典 class_info = {"name": "一班", "students": {"小明": 95, "小红": 88}}，打印班级名称和小红的成绩。
