# ===== 第081课：核心语法-面向对象基础-实例属性与类属性 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 实例属性：写在 __init__ 中，用 self.属性名 定义，每个对象各一份
#   - 类属性：直接写在类体中，属于类，所有实例共享
#   - 通过“类名.类属性”或“对象.类属性”访问
#   - 修改类属性会影响所有未单独定义同名实例属性的对象
#   - 给对象赋值同名属性会创建实例属性，不会改变类属性

class Student:
    """学生类：区分实例属性与类属性。"""

    school = "阳光中学"          # 类属性：所有学生共享
    total = 0                    # 类属性：统计学生人数

    def __init__(self, name: str, score: float) -> None:
        self.name = name         # 实例属性：每个对象独有
        self.score = score
        Student.total += 1       # 通过类名修改类属性

    def show(self) -> str:
        return f"{self.name} 就读于 {self.school}，成绩 {self.score}"

s1 = Student("小明", 92)
s2 = Student("小红", 88)

print("学校：", Student.school)
print("人数：", Student.total)
print(s1.show())
print(s2.show())

# 修改类属性，所有对象都能看到变化
Student.school = "阳光实验中学"
print("修改后：", s1.school, s2.school)

# 给 s1 单独赋值，会新增一个实例属性，只影响 s1
s1.school = "第一中学"
print("s1：", s1.school)
print("s2：", s2.school)
print("类：", Student.school)

# 查看对象和类各自的属性字典
print("s1 的属性：", s1.__dict__)
print("类的 school：", Student.__dict__["school"])

# ===== 练习题 =====
# 1. 给 Student 增加类属性 school，创建两个对象并打印学校。
# 2. 修改类属性后观察两个对象的变化，再给一个对象单独赋值。
# 3. 增加类属性 total，每创建一个对象就加 1，打印总人数。
