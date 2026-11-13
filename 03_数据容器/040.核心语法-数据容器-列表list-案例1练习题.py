# ===== 第040课：核心语法-数据容器-列表list-案例1 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 遍历列表，对每个元素进行累加、比较等处理
#   - 使用计数器统计满足条件的元素个数
#   - 使用列表下标取出第一个元素作为初始最值
#   - 平均值 = 总分 / 元素个数
#   - 综合运用 for 循环、if 判断和列表

# 某小组的 Python 成绩
scores = [88, 92, 76, 95, 61, 88, 73]

# 总分从 0 开始累加
total = 0
# 假设第一个成绩就是最高分和最低分
highest = scores[0]
lowest = scores[0]
# 及格人数从 0 开始统计
pass_count = 0

for score in scores:
    total += score
    if score > highest:
        highest = score
    if score < lowest:
        lowest = score
    if score >= 60:
        pass_count += 1

# 计算平均分
average = total / len(scores)

print("成绩列表：", scores)
print("总分：", total)
print("平均分：", average)
print("最高分：", highest)
print("最低分：", lowest)
print("及格人数：", pass_count)
print("及格率：", pass_count / len(scores) * 100)

# 找出最高分第一次出现的位置
print("最高分下标：", scores.index(highest))

# ===== 练习题 =====
# 1. 对列表 [65, 70, 85, 90, 55, 100] 求总分、平均分、最高分和最低分。
# 2. 统计上面列表中有多少人及格（>=60），并计算及格率。
# 3. 统计列表中有多少个成绩高于平均分，并打印这些成绩。
