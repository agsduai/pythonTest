# ===== 第054课：核心语法-数据容器-字典dict-案例实现 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 用“学号: 学生信息字典”的结构保存多条数据
#   - 完成添加、查询、修改、删除、遍历统计
#   - 查询前先判断键是否存在，避免报错
#   - 用 items() 遍历并统计

# ---------- 示例代码：学生成绩管理 ----------
# 1. 准备数据：键是学号，值是学生信息字典
students = {
    "001": {"name": "小明", "score": 95},
    "002": {"name": "小红", "score": 88},
    "003": {"name": "小刚", "score": 76},
}

# 2. 添加学生
students["004"] = {"name": "小美", "score": 92}
print("添加后：", students)

# 3. 查询学生（先判断学号是否存在）
sid = "002"
if sid in students:
    print("查询结果：", students[sid]["name"], students[sid]["score"])
else:
    print("学号不存在")

# 4. 修改学生成绩
students["003"]["score"] = 80
print("修改后：", students["003"])

# 5. 删除学生
removed = students.pop("004")
print("删除的学生：", removed)

# 6. 遍历统计：总分、平均分、最高分
total = 0
max_name = ""
max_score = 0
for sid, info in students.items():
    print(sid, info["name"], info["score"])
    total += info["score"]
    if info["score"] > max_score:
        max_score = info["score"]
        max_name = info["name"]
print("总分：", total, "平均分：", round(total / len(students), 2))
print("最高分：", max_score, "姓名：", max_name)

# 7. 按成绩筛选：找出 90 分及以上的学生
print("90分及以上：", [info["name"] for info in students.values() if info["score"] >= 90])

# ===== 练习题 =====
# 1. 在 students 中添加学号 "005"、姓名 "小强"、成绩 50 的学生，并打印添加后的字典。
# 2. 查询学号 "009"：如果存在就打印姓名和成绩，不存在就打印“未找到该学生”。
# 3. 统计 students 中及格（>= 60）的人数，并用列表推导式打印不及格学生的姓名。
