# ===== 第049课：核心语法-数据容器-元组tuple-案例(优化) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 用内置函数 sum()、max()、min()、len() 简化统计代码
#   - 用元组自带方法 count()、index() 完成计数和查找
#   - 用列表推导式筛选数据，再转换回元组
#   - 优化思路：能用现成方法就不手写循环，代码更短更清晰

# ---------- 示例代码：成绩统计优化版 ----------
scores = (88, 95, 72, 95, 60, 83)

# 1. 用内置函数直接求总分、最高分、最低分、平均分
total = sum(scores)                 # 求和
average = total / len(scores)       # 平均分
print("总分：", total)
print("平均分：", round(average, 2))
print("最高分：", max(scores), "最低分：", min(scores))

# 2. 用元组方法统计和查找，不必手写循环
print("95分出现次数：", scores.count(95))
print("第一个95分的下标：", scores.index(95))

# 3. 列表推导式筛选及格成绩，再转成元组
passed = tuple([s for s in scores if s >= 60])
print("及格成绩：", passed)

# 4. 列表推导式筛选不及格成绩
failed = tuple([s for s in scores if s < 60])
print("不及格成绩：", failed)

# 5. 排序：元组不可变，先转成列表，用 sort() 排序
rank = list(scores)
rank.sort(reverse=True)             # 从高到低排序
print("成绩排名：", rank)
print("前三名：", rank[:3])

# 6. 优化前后对比（思路说明）
# 优化前：for 循环累加总分、循环比较最高分、循环统计个数
# 优化后：sum()、max()、count()、index() 一行完成，逻辑更直观

# ===== 练习题 =====
# 1. 元组 nums = (23, 5, 87, 5, 42, 19)，不用循环，直接求总和、最大值、最小值和平均值。
# 2. 在上面的元组中，用 count() 统计 5 出现的次数，用 index() 找 87 的下标，并打印结果。
# 3. 元组 prices = (19, 5, 88, 36, 5, 72)，用列表推导式取出所有大于 20 的价格，转成元组后打印。
