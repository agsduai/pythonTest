# ===== 第1059课：随机数与模拟-综合案例-班级抽奖系统 =====
# 知识点：
#   - 综合运用：choice / sample / shuffle / seed / 统计
#   - 抽奖规则分层：先抽入围名单（sample），再抽大奖（choice）
#   - 防重复中奖：抽完把人从池子里移除
#   - seed 让整场抽奖结果可复现（复盘时能还原）

# 案例一：一亿元大抽奖 —— 三等奖若干、一等奖 1 名
import random

random.seed(2024)  # 可复现，方便讲解
participants = [f"同学{i:02d}" for i in range(1, 21)]

third_prize = random.sample(participants, 5)       # 三等奖 5 名（不重复）
pool2 = [p for p in participants if p not in third_prize]
second_prize = random.sample(pool2, 3)             # 二等奖 3 名
pool1 = [p for p in pool2 if p not in second_prize]
first_prize = random.choice(pool1)                 # 一等奖 1 名

print(f"三等奖：{'、'.join(third_prize)}")
print(f"二等奖：{'、'.join(second_prize)}")
print(f"一等奖：{first_prize}")

# 案例二：抽取后移除 —— 简化版防重复
# 场景：连抽 3 次"手气红包"，抽到的人退出
pool = participants[:10]
for i in range(1, 4):
    lucky = random.choice(pool)
    pool.remove(lucky)  # 关键：抽完就移除
    print(f"第 {i} 个手气王：{lucky}（剩余 {len(pool)} 人）")

# 案例三：按权重抽大奖 —— 老会员机会更大
# 场景：积分越多权重越高
members = {"小张": 3, "小李": 1, "小王": 2, "小赵": 4}
names = list(members)
weights = list(members.values())
winner = random.choices(names, weights=weights, k=1)[0]
print(f"按积分加权抽中：{winner}（积分 {members[winner]}）")

# 案例四：抽奖复盘 —— 用 seed 还原结果
# 场景：有人质疑结果，重放一遍验证
random.seed(2024)
replay = random.sample(participants, 5)
print(f"复盘重放三等奖：{'、'.join(replay)}")
print(f"与原结果一致：{replay == third_prize}")

# 案例五：整场活动串起来
def run_lottery(names, third_n, second_n, seed):
    """一次跑完三等->二等->一等奖。"""
    random.seed(seed)
    rest = list(names)
    third = random.sample(rest, third_n)
    rest = [x for x in rest if x not in third]
    second = random.sample(rest, second_n)
    rest = [x for x in rest if x not in second]
    first = random.choice(rest)
    return {"三等奖": third, "二等奖": second, "一等奖": first}

result = run_lottery(participants, 5, 3, 2024)
print(f"活动完整结果：{result}")

# ===== 练习题 =====
# 1. 20 名同学中用 sample 一次抽出 4 名"幸运观众"，保证互不相同，打印名单。
# 2. 改写案例二：改用 shuffle + 依次取前 3 个实现"连抽 3 人不重复"，验证结果不含重复。
# 3. 综合题：写函数 weighted_lottery(items, weights, n)：用 choices 抽 n 次（可重复），返回 Counter 风格的 dict 统计每人中了几次（用 dict.get 实现）。
