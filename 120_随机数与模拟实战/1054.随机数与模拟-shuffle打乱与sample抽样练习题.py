# ===== 第1054课：随机数与模拟-shuffle打乱与sample抽样 =====
# 知识点：
#   - random.shuffle(列表)：原地打乱顺序（直接改原列表，无返回值）
#   - random.sample(列表, k)：随机抽 k 个且不重复，原列表不动
#   - shuffle 适合"全部都要、只要乱序"；sample 适合"抽一部分"
#   - sample 抽超过列表长度的 k 会报 ValueError

# 案例一：shuffle 洗牌
import random

deck = [f"{r}{s}" for r in "23456789JQKA" for s in "黑红梅方"]
print(f"洗牌前前 5 张：{deck[:5]}")
random.shuffle(deck)  # 原地打乱
print(f"洗牌后前 5 张：{deck[:5]}")
print(f"发 5 张牌：{deck[:5]}")

# 案例二：sample 无重复抽样
# 场景：从 40 名学生里随机抽 3 个发言（同一人不会被抽两次）
students = [f"学生{i:02d}" for i in range(1, 41)]
speakers = random.sample(students, 3)
print(f"发言名单：{speakers}")

# 案例三：sample 抽题
# 场景：从 20 道题里随机组一套 5 题的试卷，保持题号递增可先 sorted
question_pool = [f"第{i}题" for i in range(1, 21)]
paper = sorted(random.sample(question_pool, 5))
print(f"试卷题目：{paper}")

# 案例四：shuffle 与 sample 的区别演示
nums = list(range(1, 6))
shuffled = nums[:]
random.shuffle(shuffled)  # 全量乱序
picked = random.sample(nums, 3)  # 只取 3 个
print(f"原列表：{nums}（sample 不改它）")
print(f"乱序：{shuffled}（全部 5 个，顺序变）")
print(f"抽样：{picked}（只有 3 个，不重复）")

# 案例五：分组队名 —— 打乱后切片
# 场景：8 个人随机分成两队
team_all = ["A", "B", "C", "D", "E", "F", "G", "H"]
random.shuffle(team_all)
team1, team2 = team_all[:4], team_all[4:]
print(f"红队：{team1}，蓝队：{team2}")

# ===== 练习题 =====
# 1. 生成 [1~10] 的列表，用 shuffle 打乱后打印；再验证原变量是否被修改（提示：传副本）。
# 2. 从 1~36 的号码中用 sample 抽 7 个不重复的"彩票号码"并排序输出。
# 3. 写函数 deal_cards(n)：52 张牌洗牌后发给 n 位玩家（每人 5 张），返回 {玩家: 手牌} 字典并打印。
