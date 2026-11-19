# ===== 第999课：文件操作基础-CSV文件读写 =====
# 知识点：
#   - CSV（逗号分隔值）是最常用的数据交换格式
#   - 简单方法：手动 split(",") 和 join(",")
#   - csv 模块：自动处理带引号/逗号的复杂情况
#   - csv.DictReader 按列名读取；csv.DictWriter 按列名写入
#   - newline="" 是 CSV 写入的标准写法
# 依赖：无（标准库）
import csv

# 案例一：手动读写简单 CSV
print("== 手动方式：写入 CSV ==")
students = [("张三", 85), ("李四", 92), ("王五", 78)]
with open("students.csv", "w", encoding="utf-8") as f:
    f.write("姓名,分数\n")
    for name, score in students:
        f.write(f"{name},{score}\n")
print("  已写入 students.csv")

print("\n== 手动方式：读取 CSV ==")
with open("students.csv", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        name, score = line.split(",")
        print(f"  {name}: {score} 分")

# 案例二：用 csv 模块写入
print("\n== csv 模块写入 ==")
with open("students_v2.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["姓名", "分数"])       # 表头
    writer.writerows(students)              # 批量写入多行
print("  已用 csv.writer 写入 students_v2.csv")

# 案例三：用 csv 模块读取
print("\n== csv 模块读取 ==")
with open("students_v2.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)                   # 跳过表头
    print(f"  表头: {header}")
    for row in reader:
        print(f"  {row[0]}: {row[1]} 分")

# 案例四：csv.DictReader 按列名读取
print("\n== DictReader 按列名读取 ==")
with open("students_v2.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(f"  姓名={row['姓名']}, 分数={row['分数']}")

# 案例五：csv.DictWriter 按列名写入
print("\n== DictWriter 写入 ==")
with open("students_v3.csv", "w", encoding="utf-8", newline="") as f:
    fieldnames = ["姓名", "分数", "等级"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerow({"姓名": "张三", "分数": 85, "等级": "优秀"})
    writer.writerow({"姓名": "李四", "分数": 92, "等级": "优秀"})
    writer.writerow({"姓名": "王五", "分数": 78, "等级": "良好"})
print("  已写入 students_v3.csv（含等级列）")
with open("students_v3.csv", "r", encoding="utf-8") as f:
    print(f"  内容:\n{f.read()}")

# ===== 练习题 =====
# 1. 把 5 条商品数据（名称,价格,数量）写入 products.csv。
# 2. 用 DictReader 读取 products.csv 并计算所有商品的总价。
# 3. 在 CSV 中包含一个带逗号的值（用引号包住），验证 csv 模块正确处理。
# 4. 思考：什么时候用手动 split 就够了，什么时候必须用 csv 模块？
