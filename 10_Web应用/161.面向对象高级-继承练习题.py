# ===== 第161课：面向对象高级-继承 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 继承：子类自动获得父类的属性和方法，实现代码复用
#   - 语法：class 子类(父类):
#   - 子类可以用 super().__init__() 调用父类构造方法
#   - 子类可以增加自己特有的属性和方法
#   - isinstance(对象, 类) 判断对象是否属于某类（含父类）
#   - issubclass(子类, 父类) 判断类之间的继承关系


class Person:
    """父类：保存姓名和年龄。"""

    def __init__(self, name: str, age: int) -> None:
        self.name = name
        self.age = age

    def introduce(self) -> str:
        return f"我是 {self.name}，今年 {self.age} 岁"


class Student(Person):
    """子类：学生，继承 Person。"""

    def __init__(self, name: str, age: int, student_id: str) -> None:
        super().__init__(name, age)       # 调用父类构造方法
        self.student_id = student_id       # 子类特有属性

    def study(self) -> str:
        return f"{self.name} 正在学习，学号 {self.student_id}"


class Teacher(Person):
    """子类：老师，继承 Person。"""

    def __init__(self, name: str, age: int, subject: str) -> None:
        super().__init__(name, age)
        self.subject = subject

    def teach(self) -> str:
        return f"{self.name} 正在教 {self.subject}"


student = Student("小明", 20, "S001")
teacher = Teacher("王老师", 35, "Python")
print(student.introduce())       # 直接使用父类方法
print(student.study())           # 使用子类新增方法
print(teacher.introduce())
print(teacher.teach())

print("student 是 Person：", isinstance(student, Person))
print("Student 继承 Person：", issubclass(Student, Person))

# ===== 练习题 =====
# 1. 定义 Animal 父类（name、age、eat 方法），再定义 Dog 子类继承它，
#    增加 bark 方法，并用 super().__init__ 初始化父类属性。
# 2. 定义 Vehicle 父类，Car 和 Bike 两个子类，各自增加特有方法。
# 3. 用 isinstance 判断一个 Dog 对象是否同时是 Animal 的实例。
