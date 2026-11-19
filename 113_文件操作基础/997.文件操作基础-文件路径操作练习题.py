# ===== 第997课：文件操作基础-文件路径操作 =====
# 知识点：
#   - os.path.join() 拼接路径—— 自动处理分隔符（Windows 用 \，Linux 用 /）
#   - os.path.exists() 判断文件/目录是否存在
#   - os.path.isfile() / os.path.isdir() 判断是文件还是目录
#   - os.path.getsize() 获取文件大小
#   - os.path.basename() / dirname() 拆分路径
# 依赖：无（标准库）
import os

# 案例一：拼接路径
print("== 路径拼接 ==")
folder = "data"
filename = "scores.txt"
full_path = os.path.join(folder, filename)
print(f"  os.path.join('data', 'scores.txt') = {full_path}")
print(f"  Windows 自动用 \\ 分隔，Linux 自动用 / 分隔")

# 深层路径
deep_path = os.path.join("data", "2024", "01", "scores.txt")
print(f"  深层路径: {deep_path}")

# 案例二：判断是否存在
print("\n== 判断存在 ==")
print(f"  data.txt 存在: {os.path.exists('data.txt')}")
print(f"  不存在的文件: {os.path.exists('no_such_file.txt')}")
print(f"  当前目录存在: {os.path.exists('.')}")

# 案例三：判断是文件还是目录
print("\n== 判断类型 ==")
print(f"  data.txt 是文件: {os.path.isfile('data.txt')}")
print(f"  data.txt 是目录: {os.path.isdir('data.txt')}")

# 案例四：获取文件大小
print("\n== 文件大小 ==")
size = os.path.getsize("data.txt")
print(f"  data.txt 大小: {size} 字节")
print(f"  换算: {size / 1024:.1f} KB")

# 案例五：拆分路径
print("\n== 拆分路径 ==")
test_path = os.path.join("data", "2024", "report.pdf")
print(f"  完整路径: {test_path}")
print(f"  文件名: {os.path.basename(test_path)}")
print(f"  目录部分: {os.path.dirname(test_path)}")
name_no_ext = os.path.splitext(os.path.basename(test_path))[0]
ext = os.path.splitext(os.path.basename(test_path))[1]
print(f"  无后缀文件名: {name_no_ext}, 后缀: {ext}")

# 案例六：获取当前工作目录
print(f"\n  当前工作目录: {os.getcwd()}")

# ===== 练习题 =====
# 1. 拼接路径 "logs" + "2024" + "app.log" 并打印。
# 2. 判断 "logs/app.log" 是否存在，不存在则打印提示。
# 3. 获取当前目录下任意一个文件的大小。
# 4. 思考：为什么用 os.path.join() 而不是手动写 "data/scores.txt"？
