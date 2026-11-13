# ===== 第082课：核心语法-面向对象基础-案例(教务系统-准备) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 需求：用面向对象方式管理学生信息（增、删、改、查）
#   - 设计 Student 类：学号、姓名、年龄、成绩
#   - 设计 StudentManager 类：保存学生列表，提供管理方法
#   - 先搭好类结构、菜单和入口，再逐步实现功能
#   - 数据暂时保存在内存列表中，程序结束即清空

class Student:
    """学生类：保存单个学生的信息。"""

    def __init__(self, student_id: str, name: str, age: int, score: float) -> None:
        self.student_id = student_id
        self.name = name
        self.age = age
        self.score = score

    def show(self) -> str:
        """返回一行学生信息，方便打印。"""
        return f"{self.student_id}\t{self.name}\t{self.age}\t{self.score}"

class StudentManager:
    """教务管理类：准备阶段只搭结构，方法留待后续实现。"""

    def __init__(self) -> None:
        self.students: list[Student] = []   # 用列表保存所有学生对象

    def show_menu(self) -> None:
        """打印系统菜单。"""
        print("=" * 30)
        print("1. 添加学生信息")
        print("2. 查询学生信息")
        print("3. 修改学生信息")
        print("4. 删除学生信息")
        print("5. 显示全部学生")
        print("0. 退出系统")
        print("=" * 30)

    def show_all(self) -> None:
        """显示全部学生，目前列表为空。"""
        print("学号\t姓名\t年龄\t成绩")
        for student in self.students:
            print(student.show())

# 准备阶段：创建管理对象，查看菜单和空列表
manager = StudentManager()
manager.show_menu()
print("当前学生人数：", len(manager.students))
manager.show_all()

# ===== 练习题 =====
# 1. 给 Student 增加属性 gender（性别），并在 show() 中打印。
# 2. 给 StudentManager 增加方法 count() -> int，返回学生人数。
# 3. 思考：为什么把学生列表放在 StudentManager 的 __init__ 中？
