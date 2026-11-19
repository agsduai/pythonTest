# ===== 第1066课：异常处理进阶-常见场景异常实战 =====
# 知识点：
#   - 四大高频场景：文件、JSON、字典取值、类型转换，各有典型异常
#   - 文件：FileNotFoundError；JSON：json.JSONDecodeError；取值：KeyError；转换：ValueError
#   - 处理套路：try 包住 -> 给默认值或跳过 -> 记录原因
#   - 每个场景先想清楚"失败时程序应该变成什么样"再写 except

# 案例一：文件不存在
import os, tempfile

def read_file_safe(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"文件 {path} 不存在，返回空内容")
        return ""

content = read_file_safe("不存在的文件.txt")
print(f"读取结果：{content!r}")

# 真实存在的文件能读到
tmp = os.path.join(tempfile.gettempdir(), "py_lesson_1066.txt")
with open(tmp, "w", encoding="utf-8") as f:
    f.write("hello")
print(f"正常读取：{read_file_safe(tmp)!r}")
os.remove(tmp)  # 清理

# 案例二：JSON 解析失败
import json

def parse_json_safe(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"JSON 格式错误：{e}")
        return None

print(f"合法：{parse_json_safe('{\"a\": 1}')}")
print(f"非法：{parse_json_safe('{a: 1}')}")  # 键没引号，解析失败

# 案例三：字典取值的防御
order = {"id": "A001", "amount": 99}
keys_to_read = ["id", "amount", "coupon"]
for k in keys_to_read:
    try:
        print(f"{k} = {order[k]}")
    except KeyError:
        print(f"{k} 不存在，按默认值处理")

# 一行替代方案（复习）：order.get("coupon", "无")

# 案例四：批量类型转换
# 场景：CSV 里混着空行和脏数据
rows = ["12", "3.5", "", "abc", "20"]
valid = []
for row in rows:
    try:
        valid.append(float(row))
    except ValueError:
        print(f"'{row}' 无法转数字，跳过")
print(f"有效数据：{valid}，均值 {sum(valid) / len(valid):.2f}")

# 案例五：组合拳 —— 一个接口函数处理多种异常
def load_user_data(json_text):
    """解析 JSON 并取 age 字段转整数。"""
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        return f"JSON 错误：{e}"
    try:
        return int(data["age"])
    except KeyError:
        return "缺少 age 字段"
    except (ValueError, TypeError):
        return "age 不是合法数字"

print(load_user_data('{"age": "20"}'))
print(load_user_data('{"name": "小张"}'))
print(load_user_data('{"age": "abc"}'))
print(load_user_data("bad json"))

# ===== 练习题 =====
# 1. 写 read_json_file(path)：文件不存在返回 None，内容非法返回 None，正常返回 dict；用真实临时文件测试三种情况。
# 2. 处理列表 [{"id":1,"price":"10"},{"id":2},{"id":3,"price":"abc"}]：逐条取 price 转 float，失败默认 0，最后打印价格列表与总额。
# 3. 写 safe_div(a, b)：处理除零与两个参数不是数字两种异常（TypeError），返回错误说明或结果，测试 (10,2)、(10,0)、("10",2) 三组。
