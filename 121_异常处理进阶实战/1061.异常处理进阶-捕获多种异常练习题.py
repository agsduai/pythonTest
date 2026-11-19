# ===== 第1061课：异常处理进阶-捕获多种异常 =====
# 知识点：
#   - 多个 except 从上到下匹配：谁先匹配谁处理，后面的不再看
#   - 一行捕多种：except (TypeError, ValueError) 用元组
#   - except Exception 兜底：抓所有常规异常，放最后一个分支
#   - as e 拿到异常对象：type(e).__name__ 看类型，str(e) 看信息

# 案例一：多个 except 分支 —— 不同错误不同处理
def calculator(op, a, b):
    try:
        if op == "+":
            return a + b
        if op == "/":
            return a / b
        if op == "index":
            return [a, b][int(b)]  # 故意制造越界机会
    except ZeroDivisionError:
        print(f"[{op}] 除数为 0")
    except IndexError:
        print(f"[{op}] 下标越界")
    except TypeError:
        print(f"[{op}] 类型不对（比如字符串加数字）")
    return None

calculator("+", "a", 1)   # TypeError
calculator("/", 5, 0)     # ZeroDivisionError
calculator("index", 1, 9)  # IndexError

# 案例二：元组合并捕获 —— 处理方式相同就写一行
def to_number(text):
    try:
        return int(text)
    except (ValueError, TypeError):  # int(None) 是 TypeError，int("x") 是 ValueError
        print(f"'{text}' 转不成整数")
        return 0

print(f"{to_number('12')} / {to_number('x')} / {to_number(None)}")

# 案例三：Exception 兜底 —— 保住程序不崩
# 场景：批量处理数据，任何一条出错都不能中断整批
data = ["1", "2", "abc", None, "5"]
for i, item in enumerate(data):
    try:
        value = int(item)
        print(f"第 {i} 条：{value} 处理成功")
    except Exception as e:  # 兜底：不管什么错都记录后继续
        print(f"第 {i} 条失败：{type(e).__name__}: {e}")

# 案例四：分支顺序很重要 —— 具体的在前，笼统的在后
def demo_order(x):
    try:
        return 10 / x
    except ZeroDivisionError:  # 具体异常先写
        return "除零特殊处理"
    except Exception:          # 兜底放最后
        return "其他错误"

print(f"demo(0)：{demo_order(0)}")
print(f"demo('a')：{demo_order('a')}")

# ===== 练习题 =====
# 1. 写函数 safe_get(lst, idx, d)：分别处理 IndexError 和 TypeError（idx 传字符串）两种异常，正常时返回元素。
# 2. 用元组捕获把 int() / float() 转换的 ValueError 和 TypeError 统一处理，循环处理 ["10", "3.5", None, "x"] 输出成功/失败。
# 3. 写"逐行解析器"：解析 ["8:30", "九点", "", "10:00"]（按 "时:分" 切分转数字），任何一行出错都不中断，最后统计成功行数。
