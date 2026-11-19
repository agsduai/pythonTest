# ===== 第996课：文件操作基础-逐行读取与大文件处理 =====
# 知识点：
#   - for line in 文件对象：逐行读取，内存占用小
#   - line.strip() 去掉行尾换行符
#   - enumerate(文件对象) 可以同时拿到行号
#   - 大文件不适合 read() 一次性读入—— 逐行处理是标准做法
# 依赖：无（标准库）

# 准备测试文件
with open("scores.txt", "w", encoding="utf-8") as f:
    f.write("张三,85\n李四,92\n王五,78\n赵六,95\n钱七,60\n")

# 案例一：逐行读取
print("== 逐行读取 ==")
with open("scores.txt", "r", encoding="utf-8") as f:
    for line in f:
        print(f"  {line}", end="")           # line 自带换行符，不用再加

# 案例二：带行号读取
print("\n\n== 带行号读取 ==")
with open("scores.txt", "r", encoding="utf-8") as f:
    for line_num, line in enumerate(f, start=1):
        print(f"  第{line_num}行: {line.strip()}")

# 案例三：解析每行数据
print("\n== 解析学生成绩 ==")
with open("scores.txt", "r", encoding="utf-8") as f:
    total = 0
    count = 0
    for line in f:
        line = line.strip()
        if not line:
            continue
        name, score = line.split(",")
        score = int(score)
        total += score
        count += 1
        print(f"  {name}: {score} 分")
    print(f"  平均分: {total / count:.1f}")

# 案例四：过滤——只读取分数大于 80 的
print("\n== 过滤：只显示 80 分以上的 ==")
with open("scores.txt", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        name, score_text = line.split(",")
        score = int(score_text)
        if score > 80:
            print(f"  {name}: {score} 分 ✓")

# 案例五：模拟大文件——逐行处理不占内存
print("\n== 大文件处理原则 ==")
print("  read():    一次性读入全部 → 内存 = 文件大小")
print("  readlines(): 一次性读入全部行 → 内存 = 文件大小")
print("  for line in f: 逐行处理 → 内存 = 当前行大小 ✓")
print("  100MB 的日志文件用逐行处理只需几 KB 内存")

# ===== 练习题 =====
# 1. 写入 5 行商品数据（名称,价格），逐行读取并打印「商品: 价格元」。
# 2. 统计 scores.txt 中有多少行（不用 readlines，用计数变量）。
# 3. 找出分数最高的学生并打印姓名和分数。
# 4. 思考：readlines() 和 for line in f 都能拿到全部行，什么时候该用哪个？
