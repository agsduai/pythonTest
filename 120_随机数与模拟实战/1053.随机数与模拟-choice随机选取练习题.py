# ===== 第1053课：随机数与模拟-choice随机选取 =====
# 知识点：
#   - random.choice(序列)：从列表/字符串里随机挑一个元素
#   - random.choices(序列, weights=权重, k=个数)：带权重抽多个（可重复）
#   - choice 空序列会报 IndexError，先判空再抽
#   - 实际场景：抽奖、随机点名、盲盒、按概率掉落道具

# 案例一：随机点名 / 抽奖
import random

students = ["小张", "小李", "小王", "小赵"]
print(f"今天值日：{random.choice(students)}")
print(f"幸运用户：{random.choice(students)}")

# 案例二：带权重的抽卡模拟
# 场景：普通卡 70%、稀有卡 25%、史诗卡 5%
cards = ["普通", "稀有", "史诗"]
results = random.choices(cards, weights=[70, 25, 5], k=10)
print(f"十连抽：{results}")
# 统计占比（用 str.count 简单看分布）
for c in cards:
    print(f"{c}：{results.count(c)} 张")

# 案例三：盲盒水果
# 场景：每次买一个随机水果
fruits = ["苹果", "香蕉", "橙子", "葡萄"]
bought = random.choices(fruits, k=5)
print(f"买的 5 个水果：{bought}")

# 案例四：choice 的空列表陷阱
pool = []  # 奖池抽空了
if pool:
    print(f"抽到：{random.choice(pool)}")
else:
    print("奖池为空，choice 会崩，先判断再抽")

# 案例五：随机回复语
# 场景：客服机器人随机话术
replies = [
    "亲，请问有什么可以帮您？",
    "您的问题我们已记录，稍后回复～",
    "感谢您的耐心等待！",
]
print(f"机器人说：{random.choice(replies)}")

# ===== 练习题 =====
# 1. 从 ["红", "绿", "蓝"] 中用 choice 随机挑 1 个；再用 choices 抽 20 个并统计每个颜色出现的次数。
# 2. 模拟宝箱掉落：weights=[60, 30, 10] 对应 ["金币", "宝石", "钻石"]，抽 100 次统计每种掉落数量（用 count 或循环）。
# 3. 写函数 lucky_draw(names)：列表为空返回 "没人参加"，否则随机返回一个名字；用 ["小张"] 和 [] 各测试一次。
