# ===== 第079课：核心语法-面向对象基础-实例方法 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 实例方法定义在类中，第一个参数固定为 self
#   - self 代表调用该方法的对象，用来访问实例属性
#   - 方法可以有普通参数和返回值
#   - 通过“对象.方法()”调用，不需要手动传 self
#   - 方法内部可以调用同一个类的其他方法

class Student:
    """学生类：演示实例方法的定义与调用。"""

    def __init__(self, name: str, score: float) -> None:
        self.name = name
        self.score = score

    def study(self, hours: float) -> None:
        """学习若干小时，成绩提高 2 分/小时。"""
        self.score += hours * 2
        print(f"{self.name} 学习了 {hours} 小时")

    def show_info(self) -> str:
        """返回学生信息字符串。"""
        return f"姓名：{self.name}，成绩：{self.score}"

    def is_pass(self, line: float = 60) -> bool:
        """判断是否及格，默认及格线 60 分。"""
        return self.score >= line

    def study_and_show(self, hours: float) -> None:
        """在方法中调用其他实例方法。"""
        self.study(hours)
        print(self.show_info())

s1 = Student("小明", 58)
print(s1.show_info())
print("是否及格：", s1.is_pass())

# 调用方法时不需要传 self，Python 会自动传入 s1
s1.study(2)
print(s1.show_info())
print("是否及格：", s1.is_pass(70))

s1.study_and_show(1.5)
print(s1.show_info())

# 不同的对象调用同一个方法，操作的是各自的数据
s2 = Student("小红", 90)
s2.study(1)
print(s2.show_info())

# ===== 练习题 =====
# 1. 给 Student 类增加方法 add_score(score: float) -> None，给成绩加分。
# 2. 增加方法 level() -> str，按成绩返回“优秀/及格/不及格”。
# 3. 创建两个学生，分别调用方法，观察 self 指向不同对象。
