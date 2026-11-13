# ===== 第110课：AI应用-实战-会话管理-文件操作入门 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - open() 的常用模式：r 读取、w 覆盖写入、a 追加
#   - encoding="utf-8" 保证中文读写不乱码
#   - read()、readlines() 与逐行遍历三种读取方式
#   - with 语句在代码块结束时自动关闭文件
# 依赖：无（使用 Python 内置 open 函数）

# 1. 写入文件：w 模式会清空原内容，文件不存在则创建
with open("demo.txt", "w", encoding="utf-8") as f:
    f.write("第一行：Python\n")
    f.write("第二行：AI\n")
    print("已写入：", f.name)

# 2. 读取整个文件
with open("demo.txt", "r", encoding="utf-8") as f:
    content = f.read()
print("文件内容：")
print(content)

# 3. 追加内容：a 模式在文件末尾追加，不会覆盖原内容
with open("demo.txt", "a", encoding="utf-8") as f:
    f.write("第三行：Streamlit\n")

# 4. 按行读取，适合处理较大的文件
with open("demo.txt", "r", encoding="utf-8") as f:
    for line in f:
        print("行：", line.strip())

# 5. 读取所有行到列表
with open("demo.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()
print("行数：", len(lines))

# ===== 练习题 =====
# 1. 统计 demo.txt 中一共有多少个字符（不含换行符）。
# 2. 新建 notes.txt，写入三行学习笔记，再用追加模式补一行。
# 3. 读取 demo.txt，把每一行前面加上行号后打印出来。
