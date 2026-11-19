# ===== 第994课：文件操作基础-文件写入与读取 =====
# 知识点：
#   - open("文件名", "w") 写模式：文件不存在则创建，存在则清空
#   - open("文件名", "r") 读模式：读之前文件必须存在
#   - write() 写入内容，read() 读取全部内容
#   - close() 关闭文件释放资源—— 忘了 close 可能丢数据
# 依赖：无（标准库）

# 案例一：写入文件
file = open("test_write.txt", "w", encoding="utf-8")
file.write("Hello World\n")
file.write("第二行内容\n")
file.write("第三行内容\n")
file.close()
print("已写入 test_write.txt（3 行）")

# 案例二：读取文件
file = open("test_write.txt", "r", encoding="utf-8")
content = file.read()
file.close()
print(f"\n读取全部内容:\n{content}")
print(f"内容长度: {len(content)} 字符")

# 案例三：追加模式写入
file = open("test_write.txt", "a", encoding="utf-8")
file.write("追加的第四行\n")
file.close()
print("\n追加了一行")
file = open("test_write.txt", "r", encoding="utf-8")
print(f"追加后再读取: {file.read()!r}")
file.close()

# 案例四：写入不存在路径会报错
try:
    file = open("/不存在目录/test.txt", "w")
except FileNotFoundError as e:
    print(f"\n目录不存在: {e}")

# 案例五：读取不存在的文件会报错
try:
    file = open("不存在的文件.txt", "r")
except FileNotFoundError as e:
    print(f"读取不存在的文件: {e}")

# ===== 练习题 =====
# 1. 把你的名字和年龄写入 name.txt，再读取打印出来。
# 2. 用追加模式往 name.txt 里再加一行「今天是好日子」。
# 3. 尝试打开一个不存在的目录中的文件，观察报错信息。
# 4. 思考：w 模式打开已有文件会发生什么？a 模式呢？
