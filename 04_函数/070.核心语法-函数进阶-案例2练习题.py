# ===== 第070课：核心语法-函数进阶-案例2 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 综合运用函数定义、参数、返回值、默认参数、不定长参数和 lambda
#   - 用函数组织一个完整的成绩管理小案例
#   - 列表中的字典用于保存多名学生的信息
#   - 每个函数只负责一个功能，主流程负责依次调用

students = []

def add_student(name, score):
    """添加一名学生。"""
    students.append({"name": name, "score": score})

def show_students():
    """输出全部学生成绩。"""
    print("学生成绩列表：")
    for student in students:
        print(f"  {student['name']}：{student['score']} 分")

def average_score():
    """返回平均分。"""
    if len(students) == 0:
        return 0
    scores = [student["score"] for student in students]
    return round(sum(scores) / len(scores), 2)

def top_student():
    """返回成绩最高的学生。"""
    if len(students) == 0:
        return None
    return max(students, key=lambda student: student["score"])

def pass_rate(pass_score=60):
    """返回及格率，默认及格线为 60 分。"""
    if len(students) == 0:
        return 0
    passed = [s for s in students if s["score"] >= pass_score]
    return round(len(passed) / len(students) * 100, 1)

add_student("小明", 85)
add_student("小红", 92)
add_student("小刚", 58)

show_students()
print("平均分：", average_score())
print("最高分学生：", top_student())
print("及格率：", pass_rate(), "%")
print("优秀率：", pass_rate(90), "%")

# ===== 练习题 =====
# 1. 仿照案例，用函数实现简易通讯录：add_contact(name, phone) 和 find_contact(name)。
# 2. 定义 order_total(*prices, discount=1.0)，计算任意件商品的折后总价。
# 3. 用递归实现 is_palindrome(text)，判断字符串是否为回文。
