# ===== 第087课：核心语法-异常-案例代码完善 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 给教务系统自定义异常，区分“学号重复”“学生不存在”等情况
#   - 数据校验失败时主动 raise 异常，由调用者统一处理
#   - 捕获 ValueError 处理 input 转换失败，避免程序崩溃
#   - except 从上到下匹配，先捕获子类异常再捕获父类异常
#   - 菜单交互版需要 input，可自行补充实现，运行后按提示输入
class StudentError(Exception):
    """教务系统异常基类。"""
class DuplicateStudentError(StudentError):
    """学号重复异常。"""
class StudentNotFoundError(StudentError):
    """学生不存在异常。"""
class Student:
    """学生类：创建时校验年龄和成绩。"""

    def __init__(self, student_id: str, name: str, age: int, score: float) -> None:
        if age <= 0:
            raise StudentError(f"年龄不合法：{age}")
        if not 0 <= score <= 100:
            raise StudentError(f"成绩不合法：{score}")
        self.student_id = student_id
        self.name = name
        self.age = age
        self.score = score

    def show(self) -> str:
        return f"{self.student_id}\t{self.name}\t{self.age}\t{self.score}"

class StudentManager:
    """教务管理类：用异常报告添加和查询失败。"""

    def __init__(self) -> None:
        self.students: list[Student] = []

    def add_student(self, student: Student) -> None:
        if self.find_by_id(student.student_id) is not None:
            raise DuplicateStudentError(f"学号已存在：{student.student_id}")
        self.students.append(student)

    def find_by_id(self, student_id: str) -> Student | None:
        for student in self.students:
            if student.student_id == student_id:
                return student
        return None

    def show_all(self) -> None:
        print("学号\t姓名\t年龄\t成绩")
        for student in self.students:
            print(student.show())

manager = StudentManager()
try:
    manager.add_student(Student("001", "小明", 18, 92))
    manager.add_student(Student("001", "小刚", 18, 80))
except DuplicateStudentError as e:
    print("添加失败：", e)

try:
    manager.add_student(Student("002", "小红", 19, 150))
except StudentError as e:
    print("数据不合法：", e)

try:
    raise StudentNotFoundError("学号 999 不存在")
except StudentNotFoundError as e:
    print("查询失败：", e)

manager.show_all()

# ===== 练习题 =====
# 1. 给 find_by_id 增加“找不到就抛 StudentNotFoundError”的版本。
# 2. 用 try/except 包裹 int(input())，处理用户输入非数字的情况。
# 3. 思考：为什么先捕获 DuplicateStudentError，再捕获 StudentError？
