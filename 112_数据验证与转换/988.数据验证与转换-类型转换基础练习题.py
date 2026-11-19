# ===== 第988课：数据验证与转换-类型转换基础 =====
# 知识点：
#   - int() 将字符串转整数，非数字内容会报 ValueError
#   - float() 转浮点数，可以接受 "3.14" 这种格式
#   - str() 将数字转字符串
#   - bool() 将任意值转布尔：0/""/None/[] 都是 False
#   - 转换失败要提前处理，不能让程序直接崩
# 依赖：无（标准库）

# 案例一：int 转换
print("== int() 转换 ==")
print(f"  int('123') = {int('123')}")
print(f"  int('  42  ') = {int('  42  ')}（自动去空格）")
try:
    int("abc")
except ValueError as e:
    print(f"  int('abc') -> ValueError: {e}")
try:
    int("3.14")
except ValueError as e:
    print(f"  int('3.14') -> ValueError: {e}")
print("  注意: int() 不能直接转小数格式的字符串")

# 案例二：float 转换
print("\n== float() 转换 ==")
print(f"  float('3.14') = {float('3.14')}")
print(f"  float('100') = {float('100')}（整数也能转）")
print(f"  int(float('3.14')) = {int(float('3.14'))}（先 float 再 int 截取整数）")
try:
    float("hello")
except ValueError as e:
    print(f"  float('hello') -> ValueError: {e}")

# 案例三：bool 转换规则
print("\n== bool() 转换规则 ==")
values = [0, 1, "", "hello", None, [], [1, 2], {}, False, True]
for v in values:
    print(f"  bool({v!r:>10}) = {bool(v)}")
print("  记住：0、空字符串、None、空列表、空字典 都是 False")

# 案例四：str 转换与拼接
print("\n== str() 转换 ==")
age = 25
print(f"  直接拼接会报错: '年龄' + 25")
print(f"  用 str() 转换: '年龄: ' + str(25)")
print(f"  或者用 f-string: f'年龄: {age}'")

# 案例五：安全的类型转换
def safe_int(text, default=0):
    """尝试转整数，失败返回默认值。"""
    try:
        return int(text)
    except (ValueError, TypeError):
        return default


print("\n== 安全转换函数 ==")
test_values = ["123", "abc", "45.6", "", None]
for v in test_values:
    result = safe_int(v, default=-1)
    print(f"  safe_int({v!r:>8}, default=-1) = {result}")

# ===== 练习题 =====
# 1. 把 " 99.5 " 转为浮点数再转为整数，结果是多少？
# 2. 实现 safe_float(text, default)，与 safe_int 类似。
# 3. 把 [1, 2, 3] 转为 [str(1), str(2), str(3)]，用循环实现。
# 4. 思考：为什么 int("3.14") 会报错？怎么正确地把 "3.14" 变成整数 3？
