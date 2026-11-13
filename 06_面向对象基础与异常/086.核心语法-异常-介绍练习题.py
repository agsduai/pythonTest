# ===== 第086课：核心语法-异常-介绍 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 异常是程序运行时的错误，不处理会中断程序
#   - try/except 捕获异常，except 后写异常类型
#   - else 在没有异常时执行，finally 无论是否异常都执行
#   - 常见异常：ValueError、ZeroDivisionError、KeyError、FileNotFoundError
#   - raise 可以主动抛出异常，自定义异常需继承 Exception
# 1. 除零异常
try:
    result = 10 / 0
except ZeroDivisionError as e:
    print("除零错误：", e)
# 2. 类型转换异常
try:
    number = int("abc")
except ValueError as e:
    print("数值转换失败：", e)

# 3. 字典键不存在
try:
    print({"name": "小明"}["age"])
except KeyError as e:
    print("键不存在：", e)

# 4. 文件不存在（只读打开，不会创建文件）
try:
    open("not_exist_086.txt", "r", encoding="utf-8")
except FileNotFoundError as e:
    print("文件不存在：", e)

# 5. else 与 finally
try:
    value = int("100")
except ValueError:
    print("转换失败")
else:
    print("转换成功：", value)
finally:
    print("无论成功失败都会执行 finally")

# 6. 主动抛出异常
def check_score(score: float) -> None:
    if score < 0 or score > 100:
        raise ValueError(f"成绩不合法：{score}")
    print("成绩合法：", score)

try:
    check_score(120)
except ValueError as e:
    print("捕获主动抛出的异常：", e)

# 7. 自定义异常：继承 Exception
class ScoreError(Exception):
    """成绩异常类。"""

try:
    raise ScoreError("成绩必须在 0~100 之间")
except ScoreError as e:
    print("自定义异常：", e)

# ===== 练习题 =====
# 1. 用 try/except 处理 int("abc") 的转换错误并打印提示。
# 2. 写 safe_divide(a, b)，除数为 0 时捕获异常并返回 None。
# 3. 自定义 AgeError，年龄小于 0 时 raise，并在外层捕获。
