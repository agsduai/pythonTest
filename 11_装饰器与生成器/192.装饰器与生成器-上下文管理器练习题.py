# ===== 第192课：装饰器与生成器-上下文管理器 =====
# 知识点：
#   - with 语句：进入时自动调用 __enter__，离开时自动调用 __exit__
#   - 即使 with 内部抛异常，__exit__ 也会执行 —— 保证资源一定被释放
#   - contextlib.contextmanager：用“yield 前后两段”快速实现
#   - 常见资源都可以封装成上下文管理器：文件、锁、数据库连接

import os
import time
from contextlib import contextmanager


class Timer:
    """计时上下文管理器：统计 with 块的执行耗时。"""

    def __enter__(self):
        self.start = time.perf_counter()
        return self                  # as 后面拿到的就是这个返回值

    def __exit__(self, exc_type, exc_val, exc_tb):
        cost = time.perf_counter() - self.start
        print(f"with 块耗时 {cost:.4f} 秒")
        return False                 # False：异常继续向外抛；True：吞掉异常


with Timer():
    total = sum(range(1_000_000))
print("求和结果：", total)


# 经典资源管理：保证文件一定被关闭
class SafeOpen:

    def __init__(self, path, mode="r"):
        self.path, self.mode = path, mode
        self.file = None

    def __enter__(self):
        self.file = open(self.path, self.mode, encoding="utf-8")
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()
        print("文件已关闭")
        return False


with SafeOpen("demo_192.txt", "w") as f:
    f.write("上下文管理器保证资源释放\n")
# 走到这里，文件一定已经关闭，哪怕 with 内部出过错


# contextlib 版本：yield 前相当于 __enter__，yield 后相当于 __exit__
@contextmanager
def open_guard(path, mode="r"):
    f = open(path, mode, encoding="utf-8")
    try:
        yield f                      # with 块在这里执行
    finally:
        f.close()                    # 无论是否异常都会执行


with open_guard("demo_192.txt") as f:
    print(f.read().strip())

os.remove("demo_192.txt")            # 清理演示文件


# 实用案例：给任务加“开始/完成/出错”提示
@contextmanager
def task(title):
    print(f"=== {title} 开始 ===")
    try:
        yield
    except Exception as exc:
        print(f"=== {title} 出错：{exc} ===")
        raise                        # 继续把异常抛给上层
    else:
        print(f"=== {title} 完成 ===")


with task("数据统计"):
    print("正在统计...")
    print("共 3 条记录")

# ===== 练习题 =====
# 1. 编写上下文管理器 suppress_errors，with 块内的异常被打印并吞掉
#    （提示：__exit__ 返回 True）。
# 2. 用 @contextmanager 改写 Timer，对比类的写法哪个更简洁。
# 3. 用 try + KeyboardInterrupt 演示：即使 Ctrl+C 中断，__exit__ 也会执行。
# 4. 思考：数据库连接为什么强烈建议用 with 管理？
