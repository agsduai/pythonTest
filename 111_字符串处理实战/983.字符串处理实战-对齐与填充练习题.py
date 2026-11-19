# ===== 第983课：字符串处理实战-对齐与填充 =====
# 知识点：
#   - center(宽度) 居中，ljust(宽度) 左对齐，rjust(宽度) 右对齐
#   - zfill(宽度) 左边补零 —— 常用于编号对齐
#   - f-string 的 :<^> 符号控制对齐方向
#   - 实际场景：打印表格、编号对齐、金额格式化

# 案例一：打印对齐的表格
print("== 学生成绩表 ==")
print(f"{'姓名':<10}{'语文':>6}{'数学':>6}{'英语':>6}")
students = [
    ("张三", 92, 88, 95),
    ("李四", 78, 95, 82),
    ("王五", 85, 91, 78),
]
for name, chinese, math, english in students:
    print(f"{name:<10}{chinese:>6}{math:>6}{english:>6}")

print("\n== 用 ljust / rjust 实现同样的效果 ==")
print("姓名".ljust(10) + "语文".rjust(6) + "数学".rjust(6) + "英语".rjust(6))
for name, chinese, math, english in students:
    print(name.ljust(10) + str(chinese).rjust(6)
          + str(math).rjust(6) + str(english).rjust(6))

# 案例二：编号对齐（zfill）
print("\n== 工单编号补零 ==")
for num in [1, 5, 23, 104, 999]:
    print(f"  工单号: {str(num).zfill(6)}")

# 案例三：居中显示标题
print("\n" + " 系统管理 ".center(40, "="))
print("版本 1.0.0".center(40))
print("=".center(40, "="))

# 案例四：金额格式化（千分位 + 小数位）
prices = [1234.5, 98765.43, 1000000]
print("\n== 金额格式化 ==")
print(f"{'商品':<10}{'原价':>12}{'格式化':>16}")
products = [("笔记本电脑", 5999.0), ("鼠标", 89.5), ("显示器", 1499.99)]
for name, price in products:
    print(f"  {name:<10}{price:>12.2f}  ¥{price:>14,.2f}")

# 案例五：综合——打印一张漂亮的收据
print("\n" + "=" * 40)
print("购物小票".center(38))
print("=" * 40)
items = [("苹果", 2, 5.5), ("牛奶", 1, 12.8), ("面包", 3, 8.0)]
print(f"{'商品':<10}{'数量':>6}{'单价':>10}{'小计':>10}")
print("-" * 40)
total = 0
for name, qty, price in items:
    subtotal = qty * price
    total += subtotal
    print(f"{name:<10}{qty:>6}{price:>10.1f}{subtotal:>10.1f}")
print("-" * 40)
print(f"{'合计':<10}{'':>6}{'':>10}{total:>10.1f}")
print("=" * 40)

# ===== 练习题 =====
# 1. 用 zfill 把数字 1, 42, 999 统一格式化为 4 位编号（如 0001）。
# 2. 打印一个 3 列的表格，列宽分别为 8、6、10，内容居中。
# 3. 把 1234567.891 格式化为 "1,234,567.89"（千分位 + 两位小数）。
# 4. 思考：f-string 的 :>10 和 rjust(10) 有什么区别？什么场景用哪个？
