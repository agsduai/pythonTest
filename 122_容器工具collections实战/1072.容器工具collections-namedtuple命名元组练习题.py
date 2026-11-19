# ===== 第1072课：容器工具collections-namedtuple命名元组 =====
# 知识点：
#   - namedtuple("名字", ["字段1", "字段2"])：给元组的每个位置起名字
#   - 取值用 .字段名，不用记下标 0/1/2，可读性大幅提升
#   - 内存和普通元组一样省（比 dict 小），创建仍用位置参数
#   - _replace() 生成改了字段的新对象（原对象不变，不可变思想）

# 案例一：定义并使用 —— 学生信息
from collections import namedtuple

Student = namedtuple("Student", ["name", "age", "score"])
s1 = Student("小张", 18, 92)
print(f"姓名：{s1.name}，年龄：{s1.age}，分数：{s1.score}")
print(f"整条记录：{s1}")

# 案例二：对比普通元组 —— 下标的痛
t = ("小张", 18, 92)
print(f"普通元组取年龄：{t[1]}")     # 得记住 1 是年龄
print(f"命名元组取年龄：{s1.age}")   # 名字说明一切

# 案例三：批量处理记录列表
# 场景：成绩单排序
students = [
    Student("小张", 18, 92),
    Student("小李", 19, 85),
    Student("小王", 18, 96),
]
for s in sorted(students, key=lambda st: st.score, reverse=True):
    print(f"{s.name}：{s.score} 分")

# 案例四：_replace 生成新记录
# 场景：小张补考后成绩更新
s1_new = s1._replace(score=98)
print(f"更新前：{s1.score}，更新后：{s1_new.score}")  # 原对象没变
print(f"两条记录并存：{s1} / {s1_new}")

# 案例五：坐标点运算
# 场景：2D 坐标用 namedtuple 表达
Point = namedtuple("Point", ["x", "y"])
p1, p2 = Point(1, 2), Point(3, 4)
distance_sq = (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2
print(f"两点距离：{(distance_sq ** 0.5):.2f}")

# 字段也可以用一个空格分隔的字符串定义
Color = namedtuple("Color", "red green blue")
c = Color(255, 128, 0)
print(f"颜色：R{c.red} G{c.green} B{c.blue}")

# ===== 练习题 =====
# 1. 定义 Goods = namedtuple("Goods", "name price stock")，创建 2 条商品并打印价格最高的。
# 2. 用 namedtuple 表示订单（id, amount, paid），写函数 total_paid(orders) 统计已支付订单的总金额。
# 3. 定义 Person(name, age)，用 _replace 把年龄 +1 生成新对象，验证原对象年龄不变。
