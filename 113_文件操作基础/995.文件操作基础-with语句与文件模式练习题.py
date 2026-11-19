# ===== 第995课：文件操作基础-with语句与文件模式 =====
# 知识点：
#   - with open(...) as f: 自动在结束时关闭文件，不需要手动 close
#   - "r" 读模式（默认）；"w" 写模式清空；"a" 追加模式；"x" 独占创建
#   - "r+" 读写模式：可以读也可以写
#   - "b" 二进制模式：处理图片/音频等非文本文件
#   - 文件用完必须关闭，with 语句是最安全的做法
# 依赖：无（标准库）

# 案例一：with 语句基本用法（推荐写法）
with open("data.txt", "w", encoding="utf-8") as f:
    f.write("张三,85\n")
    f.write("李四,92\n")
    f.write("王五,78\n")
print("with 写入完成，文件自动关闭")

# 案例二：with 读取
with open("data.txt", "r", encoding="utf-8") as f:
    content = f.read()
print(f"\nwith 读取全部内容:\n{content}")

# 案例三：模式对比——w 会清空，a 会追加
with open("data.txt", "w", encoding="utf-8") as f:
    f.write("覆盖模式写入\n")
print("w 模式：覆盖写入")
with open("data.txt", "r", encoding="utf-8") as f:
    print(f"当前内容: {f.read()!r}")

with open("data.txt", "a", encoding="utf-8") as f:
    f.write("追加模式写入\n")
print("a 模式：追加写入")
with open("data.txt", "r", encoding="utf-8") as f:
    print(f"当前内容: {f.read()!r}")

# 案例四：readline 与 readlines
with open("data.txt", "w", encoding="utf-8") as f:
    f.write("第一行\n第二行\n第三行\n")

with open("data.txt", "r", encoding="utf-8") as f:
    first_line = f.readline()
    print(f"\nreadline 读第一行: {first_line!r}")
    rest = f.read()
    print(f"剩余内容: {rest!r}")

with open("data.txt", "r", encoding="utf-8") as f:
    all_lines = f.readlines()
    print(f"\nreadlines 返回列表: {all_lines}")
    for i, line in enumerate(all_lines):
        print(f"  第{i + 1}行: {line.strip()}")

# 案例五：with 的好处——异常时也会关闭
try:
    with open("data.txt", "r", encoding="utf-8") as f:
        content = f.read()
        result = 1 / 0                        # 人为制造异常
except ZeroDivisionError:
    print("\n异常发生了，但 with 已自动关闭文件")
print(f"文件是否已关闭: {f.closed}")

# ===== 练习题 =====
# 1. 用 with 写入 3 行购物清单到 shopping.txt，再读取打印。
# 2. 用 "a" 模式往 shopping.txt 追加一行 "牙膏"。
# 3. 用 readline() 逐行读取 shopping.txt，打印每行内容。
# 4. 思考：为什么有了 f.close() 还需要 with 语句？如果 read() 时报错了，
#    close() 还能执行到吗？
