# ===== 第048课：核心语法-数据容器-元组tuple-案例 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 用元组保存一组固定数据（如姓名、成绩）
#   - 通过下标和 len() 遍历元组
#   - 结合循环完成总分、平均分、最高分、及格人数等统计
#   - 元组不可修改，统计时只读取数据

# ---------- 示例代码：学生成绩统计 ----------
names = ("小明", "小红", "小刚", "小美", "小强")
scores = (88, 95, 72, 95, 60)

# 1. 遍历元组求总分
total = 0
for i in range(len(scores)):
    total += scores[i]
print("总分：", total)

# 2. 求平均分（保留两位小数）
average = total / len(scores)
print("平均分：", round(average, 2))

# 3. 找出最高分及其对应姓名
max_score = scores[0]
max_index = 0
for i in range(len(scores)):
    if scores[i] > max_score:
        max_score = scores[i]
        max_index = i
print("最高分：", max_score, "姓名：", names[max_index])

# 4. 统计及格人数（成绩 >= 60）
pass_count = 0
for score in scores:
    if score >= 60:
        pass_count += 1
print("及格人数：", pass_count)

# 5. 统计 95 分出现的次数和第一次出现的下标
print("95分出现次数：", scores.count(95))
print("第一个95分的下标：", scores.index(95))

# 6. 元组切片：取前三个成绩
print("前三个成绩：", scores[:3])

# ===== 练习题 =====
# 1. 元组 scores = (88, 95, 72, 95, 55, 83)，用循环求总分和平均分并打印（平均分保留两位小数）。
# 2. 在上面的元组中统计不及格（< 60）的人数，并打印所有不及格的成绩。
# 3. 元组 fruits = ("苹果", "香蕉", "苹果", "橙子", "苹果")，统计“苹果”出现的次数和第一次出现的下标。
