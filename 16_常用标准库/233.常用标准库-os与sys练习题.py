# ===== 第233课：常用标准库-os与sys =====
# 知识点：
#   - os：操作系统交互 —— 目录、环境变量、文件增删、CPU 核数
#   - os.environ：读取环境变量（第098课的 API_KEY 就是这么拿的）
#   - sys：解释器交互 —— 命令行参数、模块搜索路径、退出码
#   - os.name 区分系统：nt=Windows，posix=Linux/Mac

import os
import sys

print("当前目录：", os.getcwd())
print("系统类型：", os.name)
print("CPU 核数：", os.cpu_count())

# 环境变量：配置与代码分离的常用手段
os.environ.setdefault("DEMO_VAR_233", "hello")
print(os.getenv("DEMO_VAR_233", "默认值"))
print("PATH 存在：", "PATH" in os.environ)

# 文件与目录操作
os.makedirs("os_demo/sub", exist_ok=True)
with open("os_demo/a.txt", "w", encoding="utf-8") as f:
    f.write("demo")
print("目录内容：", os.listdir("os_demo"))
print("文件大小：", os.path.getsize("os_demo/a.txt"), "字节")
os.remove("os_demo/a.txt")
os.removedirs("os_demo/sub")       # 删除空目录（含父级）

# sys：命令行参数与解释器信息
print("命令行参数：", sys.argv)     # 运行 python xxx.py a b 时能看到 a b
print("模块搜索路径条数：", len(sys.path))
print("递归深度限制：", sys.getrecursionlimit())
print("解释器路径：", sys.executable)

# 说明：sys.exit(0) 正常退出；sys.exit(非0) 表示异常退出，脚本常配合参数校验

# ===== 练习题 =====
# 1. 打印当前目录下所有 .py 文件的名字（os.listdir + endswith）。
# 2. 编写函数 read_env(key)：环境变量不存在时抛 ValueError。
# 3. 用 sys.argv 写一个 greeting.py：python greeting.py 小明 输出“你好，小明”。
# 4. 思考：os 和 pathlib、os.path 各自的分工？
