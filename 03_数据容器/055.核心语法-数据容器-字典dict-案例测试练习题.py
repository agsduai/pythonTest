# ===== 第055课：核心语法-数据容器-字典dict-案例测试 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 用 if 判断实际结果是否等于预期结果
#   - 测试新增、查询、修改、删除是否正确
#   - 测试统计结果（平均分）是否正确
#   - 测试要覆盖正常数据和不存在的数据

# ---------- 示例代码：给学生成绩管理写测试 ----------
students = {
    "001": {"name": "小明", "score": 95},
    "002": {"name": "小红", "score": 88},
    "003": {"name": "小刚", "score": 76},
}

# 测试1：查询已有学生
if students["001"]["name"] == "小明" and students["002"]["score"] == 88:
    print("测试1 查询：通过")
else:
    print("测试1 查询：失败")

# 测试2：新增学生
students["004"] = {"name": "小美", "score": 92}
if "004" in students and students["004"]["name"] == "小美":
    print("测试2 新增：通过")
else:
    print("测试2 新增：失败")

# 测试3：修改成绩
students["003"]["score"] = 80
if students["003"]["score"] == 80:
    print("测试3 修改：通过")
else:
    print("测试3 修改：失败")

# 测试4：删除学生
removed = students.pop("004")
if removed["name"] == "小美" and "004" not in students:
    print("测试4 删除：通过")
else:
    print("测试4 删除：失败")

# 测试5：统计平均分
total = 0
for info in students.values():
    total += info["score"]
average = round(total / len(students), 2)
if average == round((95 + 88 + 80) / 3, 2):
    print("测试5 统计：通过，平均分 =", average)
else:
    print("测试5 统计：失败")

# 测试6：查询不存在的键要用 get() 兜底
if students.get("009") is None:
    print("测试6 不存在键：通过")
else:
    print("测试6 不存在键：失败")

print("测试执行完毕，请检查每个测试是否通过。")

# ===== 练习题 =====
# 1. 给字典 goods = {"苹果": 5, "香蕉": 3} 写测试：判断苹果数量是否为 5、香蕉数量是否为 3。
# 2. 修改苹果数量为 8、删除香蕉，再用 if 判断修改和删除的结果是否正确。
# 3. 字典 scores = {"语文": 90, "数学": 88, "英语": 92}，计算平均分并判断平均分是否等于 90.0。
