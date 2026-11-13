# ===== 第084课：核心语法-面向对象基础-案例(教务系统-修改删除查询) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 查询：遍历列表，按学号找到学生对象；找不到返回 None
#   - 修改：先查到对象，再修改它的属性
#   - 删除：先查到对象，再用列表 remove() 删除
#   - 所有操作都返回 bool 或对象，方便调用者判断结果
#   - 字符串比较用 ==，判断 None 用 is None
class Student:
    """学生类：保存单个学生的信息。"""

    def __init__(self, student_id: str, name: str, age: int, score: float) -> None:
        self.student_id = student_id
        self.name = name
        self.age = age
        self.score = score

    def show(self) -> str:
        return f"{self.student_id}\t{self.name}\t{self.age}\t{self.score}"

class StudentManager:
    """教务管理类：实现增、查、改、删。"""

    def __init__(self) -> None:
        self.students: list[Student] = []

    def add_student(self, student: Student) -> bool:
        for item in self.students:
            if item.student_id == student.student_id:
                print("学号已存在：", student.student_id)
                return False
        self.students.append(student)
        return True

    def find_by_id(self, student_id: str) -> Student | None:
        """按学号查询，找到返回学生对象，否则返回 None。"""
        for student in self.students:
            if student.student_id == student_id:
                return student
        return None

    def update_student(self, student_id: str, name: str, score: float) -> bool:
        """修改姓名和成绩，找不到返回 False。"""
        student = self.find_by_id(student_id)
        if student is None:
            return False
        student.name, student.score = name, score
        return True

    def delete_student(self, student_id: str) -> bool:
        """按学号删除，找不到返回 False。"""
        student = self.find_by_id(student_id)
        if student is None:
            return False
        self.students.remove(student)
        return True

    def show_all(self) -> None:
        print("学号\t姓名\t年龄\t成绩")
        for student in self.students:
            print(student.show())

manager = StudentManager()
manager.add_student(Student("2025001", "小明", 18, 92.5))
manager.add_student(Student("2025002", "小红", 19, 88.0))
manager.add_student(Student("2025003", "小刚", 18, 75.0))

print("查询结果：", manager.find_by_id("2025002").show())
print("修改成功：", manager.update_student("2025002", "小红", 95.0))
print("删除成功：", manager.delete_student("2025003"))
print("删除不存在的学号：", manager.delete_student("9999999"))
manager.show_all()

# ===== 练习题 =====
# 1. 添加 3 个学生，按学号查询其中一个并打印信息。
# 2. 修改某个学生的成绩，再查询确认修改结果。
# 3. 删除一个学生后调用 show_all()，验证列表已更新。
