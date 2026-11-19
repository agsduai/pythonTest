# ===== 第1058课：随机数与模拟-模拟测试数据生成 =====
# 知识点：
#   - 写程序时常用"假数据"测试：姓名、年龄、手机号、成绩、订单
#   - 组合多个随机源 + zip/推导式，批量生成结构化假数据
#   - sample 抽名字保证不重复；randint 生成数值字段
#   - 假数据用于开发调试，正式数据必须来自真实来源

# 案例一：随机生成一个"用户"
import random

surnames = ["张", "李", "王", "刘", "陈"]
givens = ["伟", "芳", "娜", "军", "磊", "静"]
cities = ["北京", "上海", "广州", "深圳"]

def make_user():
    return {
        "name": random.choice(surnames) + random.choice(givens),
        "age": random.randint(18, 45),
        "city": random.choice(cities),
    }

print(f"随机用户：{make_user()}")

# 案例二：批量生成并展示
# 场景：给页面造 5 条测试数据
users = [make_user() for _ in range(5)]
for u in users:
    print(f"{u['name']}，{u['age']} 岁，来自{u['city']}")

# 案例三：不重复的名字抽样
# 场景：3 位中奖者不能重名
name_pool = [f"{s}{g}" for s in surnames for g in givens]
winners = random.sample(name_pool, 3)
print(f"中奖名单：{winners}")

# 案例四：生成班级成绩表
# 场景：30 名学生、3 科成绩，用于后续统计练习
random.seed(7)  # 固定种子，练习数据可复现
students = []
for i in range(1, 31):
    students.append({
        "id": f"S{i:03d}",
        "chinese": random.randint(40, 100),
        "math": random.randint(40, 100),
        "english": random.randint(40, 100),
    })
top = max(students, key=lambda s: s["chinese"] + s["math"] + s["english"])
print(f"总分第一名：{top['id']}，总分 {top['chinese'] + top['math'] + top['english']}")

# 案例五：模拟订单流水
# 场景：10 笔随机订单（商品随机、金额随商品定价走）
catalog = {"苹果": 5.5, "牛奶": 8.0, "面包": 12.0}
orders = []
for i in range(1, 11):
    goods = random.choice(list(catalog))
    count = random.randint(1, 5)
    orders.append((f"O{i:03d}", goods, count, round(catalog[goods] * count, 2)))
for o in orders[:5]:
    print(f"订单 {o[0]}：{o[1]} x{o[2]} = {o[3]} 元")
print(f"10 笔订单总额：{round(sum(o[3] for o in orders), 2)} 元")

# ===== 练习题 =====
# 1. 生成 8 个 1~100 的随机成绩列表，打印平均分（保留 1 位小数）与及格人数。
# 2. 写函数 make_phone()：返回形如 "138" + 8 位随机数字的手机号（1[3-9] 开头简化为 13x~19x 随机即可），生成 3 个。
# 3. 组合题：生成 10 个 {姓名, 科目, 分数} 的考试记录（科目从 3 科随机），按科目分组打印平均分。
