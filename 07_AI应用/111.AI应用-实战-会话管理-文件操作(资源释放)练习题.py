# ===== 第111课：AI应用-实战-会话管理-文件操作(资源释放) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 文件打开后会占用系统资源，用完必须关闭
#   - try/finally 保证发生异常时也能 close()
#   - with 上下文管理器在代码块结束时自动关闭文件（推荐）
#   - 一次 with 可以同时管理多个文件
# 依赖：无（使用 Python 内置 open 函数）

# 方式一：手动打开和关闭。若 write 抛异常，close 可能执行不到
f = open("demo.txt", "w", encoding="utf-8")
try:
    f.write("hello\n")
finally:
    f.close()  # finally 保证一定关闭
print("手动关闭后 f.closed =", f.closed)

# 方式二：with 上下文管理器，离开代码块自动关闭（推荐）
with open("demo.txt", "a", encoding="utf-8") as f:
    f.write("world\n")
print("with 结束后 f.closed =", f.closed)

# 读取验证
with open("demo.txt", "r", encoding="utf-8") as f:
    print(f.read())

# 同时打开多个文件：with 可以一次管理多个资源
with open("demo.txt", "r", encoding="utf-8") as src, \
        open("copy.txt", "w", encoding="utf-8") as dst:
    dst.write(src.read())
print("复制完成")

# ===== 练习题 =====
# 1. 故意在 with 代码块中抛出异常，确认文件仍然会被关闭。
# 2. 把方式一改写成 try/except/finally，捕获写入异常并打印提示。
# 3. 用 with 同时读取 demo.txt、写入 backup.txt，实现文件备份。
