# ===== 第990课：数据验证与转换-数值范围检查与默认值 =====
# 知识点：
#   - min() / max() 可以做范围截断：min(max(值, 下限), 上限)
#   - or 提供默认值：值 or 默认值（但 0 和 "" 也是 falsy，要小心）
#   - try/except + int() 组合是标准的输入转换模式
#   - 合法范围检查用 and 连接上下界
# 依赖：无（标准库）

# 案例一：范围截断
temperature = 45
CLAMP_MIN, CLAMP_MAX = 0, 30
clamped = min(max(temperature, CLAMP_MIN), CLAMP_MAX)
print(f"温度 {temperature} -> 截断后 {clamped}")

temperature = -10
clamped = min(max(temperature, CLAMP_MIN), CLAMP_MAX)
print(f"温度 {temperature} -> 截断后 {clamped}")

print("\n== 用函数封装截断 ==")
def clamp(value, lo, hi):
    return min(max(value, lo), hi)


for v in [-5, 0, 15, 30, 50]:
    print(f"  clamp({v}, 0, 30) = {clamp(v, 0, 30)}")

# 案例二：默认值的陷阱
print("\n== or 提供默认值的陷阱 ==")
count = 0
default_count = count or 10            # 0 是 falsy -> 用了默认值 10
print(f"  count = 0, count or 10 = {default_count}（0 被覆盖了！）")
count = 5
default_count = count or 10
print(f"  count = 5, count or 10 = {default_count}")
print("  正确做法：显式判断 None")
count = 0
if count is None:
    count = 10
print(f"  显式判断后 count = {count}")

# 案例三：评分范围检查
print("\n== 成绩范围检查 ==")
scores = [85, 120, -5, 0, 60, 100]
for score in scores:
    if 0 <= score <= 100:
        grade = "优秀" if score >= 90 else ("良好" if score >= 80 else ("及格" if score >= 60 else "不及格"))
        print(f"  {score:>4} -> {grade}")
    else:
        print(f"  {score:>4} -> 无效成绩（超出 0-100）")

# 案例四：数据修正——把超出范围的值拉回边界
print("\n== 传感器数据修正 ==")
readings = [-2, 0, 15, 32, 100, 105]
MIN, MAX = 0, 100
print(f"  原始数据: {readings}")
corrected = [min(max(r, MIN), MAX) for r in readings]
print(f"  修正后:   {corrected}")
print("  超出量程的值被『钳』到了边界 —— 这叫 clamping")

# 案例五：带默认值的配置读取
print("\n== 配置读取与默认值 ==")
config = {"timeout": 30, "retries": 3}
# 读取存在的配置
timeout = config.get("timeout", 10)
retries = config.get("retries", 5)
# 读取不存在的配置
max_retry = config.get("max_retry", 3)
debug = config.get("debug", False)
print(f"  timeout = {timeout}, retries = {retries}")
print(f"  max_retry = {max_retry}（默认 3）, debug = {debug}（默认 False）")

# ===== 练习题 =====
# 1. 用 clamp 函数把 [-10, 5, 50, 100] 截断到 [0, 60] 范围。
# 2. 实现 safe_divide(a, b)：b 为 0 时返回默认值 0 而不是报错。
# 3. 读取 config 字典中的 "port" 键，如果不存在默认 8080，且限制在 1-65535。
# 4. 思考：count or 10 在什么场景下是安全的？什么时候会出 bug？
