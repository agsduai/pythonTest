# ===== 第1027课：推导式与内置函数-综合案例-成绩统计 =====
# 知识点：
#   - 推导式 + 内置函数组合：真实统计任务几乎是它们的流水线
#   - 常用内置函数：sum / max / min / len / round / any / all
#   - any(条件 for x in 数据)：有一个满足就 True；all：全部满足才 True
#   - 数据清洗先行：转数字、去空格、剔非法值，再统计才有意义

# 案例一：全班成绩统计 —— 一条流水线搞定
# 场景：成绩表是字符串带空格的脏数据
raw_scores = [" 88 ", "92", "abc", "75", "", " 59 "]
# 第 1 步：清洗 + 转数字（推导式过滤 + float 转换）
scores = [float(s.strip()) for s in raw_scores if s.strip().isdigit()]
print(f"清洗后成绩：{scores}")  # [88.0, 92.0, 75.0, 59.0]

# 第 2 步：一步算出所有统计值
print(f"最高：{max(scores)}，最低：{min(scores)}，平均：{round(sum(scores) / len(scores), 1)}")

# 案例二：any / all —— 快速判断
# 场景：有没有人不及格？是不是全班都及格了？
print(f"有人不及格：{any(s < 60 for s in scores)}")   # True
print(f"全班都及格：{all(s >= 60 for s in scores)}")  # False

# 案例三：分级统计 —— 推导式 + 字典 + 条件
# 场景：按优秀/及格/不及格分档
students = {"小张": 88, "小李": 45, "小王": 92, "小赵": 73}
levels = {name: ("优秀" if s >= 80 else "及格" if s >= 60 else "不及格")
          for name, s in students.items()}
print(f"等级表：{levels}")

# 案例四：按等级分组 —— setdefault + 循环
groups = {}
for name, s in students.items():
    level = "优秀" if s >= 80 else "及格" if s >= 60 else "不及格"
    groups.setdefault(level, []).append(name)
print(f"分组：{groups}")
for level, names in sorted(groups.items()):
    print(f"{level}（{len(names)} 人）：{'、'.join(names)}")

# 案例五：排行榜 —— sorted + lambda 多条件
# 按分数降序取前三名
ranking = sorted(students.items(), key=lambda kv: kv[1], reverse=True)[:3]
for i, (name, s) in enumerate(ranking, start=1):
    print(f"第 {i} 名：{name}（{s} 分）")

# ===== 练习题 =====
# 1. 用推导式从 ["12", "x", "30", "", "45"] 中提取数字并输出 [12, 30, 45] 及它们的平均值 29.0。
# 2. 用 any/all 判断列表 [80, 92, 75]：是否全部 >= 80？是否有任何一科 < 70？输出 True/False。
# 3. 商品字典 {"苹果": 5.5, "牛奶": 8.0, "面包": 12.0, "酸奶": 15.0}，用字典推导式筛出价格 >= 8 的商品，并用 sorted 按价格降序打印每项。
