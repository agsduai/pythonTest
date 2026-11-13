# ===== 第071课：核心语法-类型注解-介绍 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 类型注解是写给开发者和 IDE 看的“类型提示”，运行时不强制检查
#   - 变量注解语法：变量名: 类型 = 值
#   - 常见注解：int、float、str、bool、list[int]、dict[str, int]
#   - 联合类型：int | None 表示整数或空值
#   - 注解能提升代码可读性，并让编辑器给出更准确的提示

# 基本类型注解
name: str = "小明"
age: int = 18
height: float = 1.75
is_student: bool = True

# 容器类型注解：说明容器里装的是什么类型
scores: list[int] = [90, 85, 88]
profile: dict[str, object] = {"name": name, "age": age}
point: tuple[int, int] = (3, 5)

# 联合类型：nickname 可能是字符串，也可能是 None
nickname: str | None = None

# 注解只是提示，赋了不同类型的值也不会报错
age = "十八"
print(name, age, height, is_student)
print(scores, profile, point, nickname)

# 函数也可以写类型注解，下一课会详细学习
def greet(person: str) -> str:
    """接收姓名，返回问候语。"""
    return "你好，" + person

print(greet(name))

# ===== 练习题 =====
# 1. 为图书信息写注解：书名 str、价格 float、库存 int、标签 list[str]。
# 2. 声明变量 author: str | None = None，判断为空时打印“作者未知”。
# 3. 给函数 total(price, count) 补上参数和返回值注解，并计算总价。
