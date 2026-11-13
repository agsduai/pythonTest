# ===== 第083课：核心语法-面向对象基础-案例(教务系统-添加学生信息) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 添加学生：把 Student 对象追加到管理器的列表中
#   - 学号唯一：添加前先遍历列表检查是否重复
#   - 方法返回 bool 表示添加是否成功
#   - 把“创建对象”和“保存对象”分成两步，逻辑更清晰
#   - 列表 append() 追加元素，len() 获取学生人数

class Student:
    """学生类：保存单个学生的信息。"""

    def __init__(self, student_id: str, name: str, age: int, score: float) -> None:
        self.student_id = student_id
        self.name = name
        self.age = age
        self.score = score

    def show(self) -> str:
        """返回一行学生信息。"""
        return f"{self.student_id}\t{self.name}\t{self.age}\t{self.score}"

class StudentManager:
    """教务管理类：实现添加和显示功能。"""

    def __init__(self) -> None:
        self.students: list[Student] = []

    def add_student(self, student: Student) -> bool:
        """添加学生，学号重复则返回 False。"""
        for item in self.students:
            if item.student_id == student.student_id:
                print("添加失败：学号已存在")
                return False
        self.students.append(student)
        print("添加成功：", student.name)
        return True

    def show_all(self) -> None:
        """打印全部学生。"""
        print("学号\t姓名\t年龄\t成绩")
        for student in self.students:
            print(student.show())

manager = StudentManager()
manager.add_student(Student("2025001", "小明", 18, 92.5))
manager.add_student(Student("2025002", "小红", 19, 88.0))
manager.add_student(Student("2025001", "小刚", 18, 75.0))   # 学号重复
manager.show_all()
print("学生人数：", len(manager.students))

# ===== 练习题 =====
# 1. 创建 3 个学生对象，用循环调用 add_student 批量添加，并统计成功数量。
# 2. 添加前检查成绩是否在 0~100，不合法则打印提示并跳过。
# 3. 思考：为什么先检查学号重复，再执行 append()？
