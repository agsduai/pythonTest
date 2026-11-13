# ===== 第078课：核心语法-面向对象基础-类与对象 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - class 类名: 定义类，类名建议用大驼峰命名
#   - __init__ 是初始化方法，创建对象时自动调用
#   - self 表示当前对象，是实例方法的第一个参数
#   - 对象名.属性 访问属性，对象名.方法() 调用方法
#   - 每次创建对象都会执行一次 __init__，不同对象属性互相独立

class Student:
    """学生类：保存学号、姓名、年龄和成绩。"""

    def __init__(self, student_id: str, name: str, age: int, score: float) -> None:
        # self.xxx 表示给当前对象保存属性
        self.student_id = student_id
        self.name = name
        self.age = age
        self.score = score

# 创建对象时传入 __init__ 需要的参数
s1 = Student("2025001", "小明", 18, 92.5)
s2 = Student("2025002", "小红", 19, 88.0)

print(s1.student_id, s1.name, s1.age, s1.score)
print(s2.student_id, s2.name, s2.age, s2.score)

# 属性可以修改
s2.score = 90.0
print("小红的成绩：", s2.score)

# 两个对象的属性互不影响
s1.name = "小刚"
print(s1.name, s2.name)

# 查看对象属性字典
print(s1.__dict__)

# 对象也可以作为列表元素，方便批量管理
students = [s1, s2]
for student in students:
    print(student.student_id, student.name, student.score)

# ===== 练习题 =====
# 1. 定义 Book 类，__init__ 接收 title、price、author 并保存为属性。
# 2. 创建两本书对象，修改其中一本的价格，打印两本书的信息。
# 3. 把两本书放进列表，用 for 循环打印每本书的书名和价格。
