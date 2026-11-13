# ===== 第072课：核心语法-类型注解-函数的类型注解 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 参数注解：def 函数名(参数名: 类型)
#   - 返回值注解：def 函数名(...) -> 类型
#   - 函数没有返回值时写 -> None
#   - 默认参数、容器参数和字典参数都可以写注解
#   - 类型注解不会在运行时强制校验，只用于提示

# 两个参数都是 int，返回值也是 int
def add(a: int, b: int) -> int:
    """返回两个整数之和。"""
    return a + b

# 字符串和浮点参数，返回字符串
def format_score(name: str, score: float) -> str:
    """把姓名和分数拼成一句话。"""
    return f"{name} 的成绩是 {score} 分"

# 没有返回值，用 None 标注
def print_line(text: str, width: int = 20) -> None:
    """打印带分隔线的标题。"""
    print("=" * width)
    print(text)
    print("=" * width)

# 列表参数：列表中的元素是 float
def average(numbers: list[float]) -> float:
    """求平均值，空列表返回 0。"""
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)

# 字典参数 + 可能找不到的返回值
def find_score(students: dict[str, int], name: str) -> int | None:
    """按姓名查分数，找不到返回 None。"""
    return students.get(name)

print(add(3, 5))
print(format_score("小明", 92.5))
print_line("成绩单")
print("平均分：", average([90.0, 85.5, 88.0]))
print("小红的分数：", find_score({"小明": 92, "小刚": 78}, "小红"))

# ===== 练习题 =====
# 1. 为 circle_area(r) 补全参数和返回值注解，返回圆的面积。
# 2. 写函数 show_students(students: list[dict[str, object]]) -> None 打印学生信息。
# 3. 写带默认参数的 power(base: int, exp: int = 2) -> int，并调用验证。
