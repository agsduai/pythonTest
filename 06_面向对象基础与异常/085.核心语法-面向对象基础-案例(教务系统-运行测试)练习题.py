# ===== 第085课：核心语法-面向对象基础-案例(教务系统-运行测试) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 用 while True + input 实现菜单循环
#   - 根据用户输入调用对应的方法
#   - 用 if/elif/else 分发菜单选项
#   - 选择退出时用 break 结束循环
#   - 菜单交互版需要 input，可自行补充实现，运行后按提示输入
class Student:
    """学生类：保存学号、姓名、年龄和成绩。"""
    def __init__(self, student_id: str, name: str, age: int, score: float) -> None:
        self.student_id = student_id
        self.name = name
        self.age = age
        self.score = score
    def show(self) -> str:
        return f"{self.student_id}\t{self.name}\t{self.age}\t{self.score}"
class StudentManager:
    """教务管理类：提供增、查、改、删操作。"""

    def __init__(self) -> None:
        self.students: list[Student] = []

    def add_student(self, student: Student) -> bool:
        if self.find_by_id(student.student_id) is not None:
            return False
        self.students.append(student)
        return True
    def find_by_id(self, student_id: str) -> Student | None:
        for student in self.students:
            if student.student_id == student_id:
                return student
        return None

    def update_student(self, student_id: str, name: str, score: float) -> bool:
        student = self.find_by_id(student_id)
        if student is None:
            return False
        student.name, student.score = name, score
        return True

    def delete_student(self, student_id: str) -> bool:
        student = self.find_by_id(student_id)
        if student is None:
            return False
        self.students.remove(student)
        return True
def demo() -> None:
    """不依赖输入的自测：模拟添加、修改、删除和显示。"""
    manager = StudentManager()
    manager.add_student(Student("2025001", "小明", 18, 92.5))
    manager.add_student(Student("2025002", "小红", 19, 88.0))
    print("重复添加：", manager.add_student(Student("2025001", "小刚", 18, 70)))
    print("修改：", manager.update_student("2025002", "小红", 95.0))
    print("删除：", manager.delete_student("2025001"))
    for student in manager.students:
        print(student.show())
    print("剩余人数：", len(manager.students))
demo()

# ===== 练习题 =====
# 1. 给 demo() 增加一次“查询不存在的学号”，观察返回值。
# 2. 用 while True + input 把 StudentManager 包装成菜单循环，
#    实现 1~5 和 0 号功能（1添加 2查询 3修改 4删除 0退出）。
# 3. 思考：为什么 input() 得到的年龄、成绩要转成 int、float？
