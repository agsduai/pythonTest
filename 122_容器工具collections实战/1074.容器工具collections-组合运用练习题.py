# ===== 第1074课：容器工具collections-组合运用 =====
# 知识点：
#   - 真实任务常常几个工具一起上：Counter + defaultdict + namedtuple
#   - namedtuple 做"数据结构"，defaultdict 做"归类"，Counter 做"统计"
#   - 选择口诀：要名字用 namedtuple、要分组用 defaultdict、要计数用 Counter
#   - 组合时先想清楚"数据的形状"：谁装谁、键是什么、值是什么

# 案例一：订单分析三件套
from collections import Counter, defaultdict, namedtuple

Order = namedtuple("Order", ["id", "user", "goods", "amount"])
orders = [
    Order("O1", "小张", "苹果", 15.5),
    Order("O2", "小李", "牛奶", 24.0),
    Order("O3", "小张", "牛奶", 24.0),
    Order("O4", "小王", "苹果", 15.5),
    Order("O5", "小张", "面包", 12.0),
]

# 1) Counter：谁下过最多单
user_orders = Counter(o.user for o in orders)
print(f"下单次数：{user_orders.most_common()}")

# 2) defaultdict：每人买了什么
user_goods = defaultdict(list)
for o in orders:
    user_goods[o.user].append(o.goods)
print(f"购买清单：{dict(user_goods)}")

# 3) defaultdict + float：每人消费总额
user_spent = defaultdict(float)
for o in orders:
    user_spent[o.user] += o.amount
print(f"消费总额：{dict(user_spent)}")

# 案例二：课程签到统计 —— namedtuple + Counter
Checkin = namedtuple("Checkin", ["student", "day", "late"])
records = [
    Checkin("小张", "周一", False), Checkin("小李", "周一", True),
    Checkin("小张", "周二", False), Checkin("小王", "周二", True),
    Checkin("小李", "周三", True),
]
late_counter = Counter(r.student for r in records if r.late)
print(f"迟到统计：{dict(late_counter)}")

# 案例三：商品销售分组排行 —— defaultdict 收集 + Counter 汇总
sales_rows = [
    ("食品", "苹果"), ("食品", "面包"), ("数码", "耳机"),
    ("食品", "苹果"), ("数码", "充电器"), ("食品", "苹果"),
]
by_category = defaultdict(list)
for cat, goods in sales_rows:
    by_category[cat].append(goods)
for cat, goods_list in by_category.items():
    print(f"{cat} 类 Top 商品：{Counter(goods_list).most_common(1)[0]}")

# 案例四：组合小项目 —— 班级成绩册
Student = namedtuple("Student", ["name", "subject", "score"])
grade_rows = [
    Student("小张", "数学", 92), Student("小张", "英语", 85),
    Student("小李", "数学", 78), Student("小李", "英语", 90),
    Student("小王", "数学", 88),
]
gradebook = defaultdict(dict)  # 学生 -> {科目: 分数}
for r in grade_rows:
    gradebook[r.name][r.subject] = r.score
for name, subjects in gradebook.items():
    avg = sum(subjects.values()) / len(subjects)
    print(f"{name}：{subjects}，平均 {avg:.1f}")

# ===== 练习题 =====
# 1. 用 namedtuple 定义 Expense(date, category, amount)，造 5 条记录，用 defaultdict(float) 按品类汇总金额。
# 2. 用 Counter 统计练习 1 中"哪天花钱次数最多"，输出 (日期, 次数)。
# 3. 综合：学生记录 namedtuple(name, subject, score)，用 defaultdict(list) 按科目分组后，打印每科最高分学生姓名。
