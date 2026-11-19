# ===== 第1065课：异常处理进阶-记录异常信息 =====
# 知识点：
#   - as e 拿到异常对象：str(e) 是提示信息，type(e).__name__ 是类型名
#   - logging.error(..., exc_info=True) 或 logging.exception：连堆栈一起记
#   - traceback.print_exc() 打印完整堆栈（调试期快速排查）
#   - 生产环境"记录后继续"代替"崩溃"，事后能从日志还原现场

# 案例一：异常对象的基本用法
def show_error(a, b):
    try:
        return a / b
    except ZeroDivisionError as e:
        print(f"类型名：{type(e).__name__}")
        print(f"信息：{e}")
        print(f"repr 形式：{e!r}")
        return None

show_error(1, 0)

# 案例二：logging 记录异常
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("demo")

def risky_task(data):
    try:
        value = int(data)
        return value
    except ValueError:
        logger.error(f"解析 '{data}' 失败", exc_info=True)  # 带堆栈
        return None

risky_task("abc")

# 案例三：traceback.print_exc 快速打印
import traceback

def deep_divide():
    return 1 / 0

def run_task():
    try:
        deep_divide()
    except ZeroDivisionError:
        print("--- 堆栈信息 ---")
        traceback.print_exc()  # 打印完整调用链，和报错时一样
        print("--- 处理完成，程序继续 ---")

run_task()
print("程序没有崩溃，继续运行")

# 案例四：异常信息写入列表（简易日志系统）
# 场景：批处理任务汇总所有失败项
error_log = []

def process(items):
    for i, item in enumerate(items):
        try:
            if item < 0:
                raise ValueError("不能为负数")
            print(f"处理第 {i} 项：{item} OK")
        except (ValueError, TypeError) as e:
            error_log.append({"index": i, "type": type(e).__name__, "msg": str(e)})

process([1, -2, "x", 4])
print("--- 错误日志 ---")
for row in error_log:
    print(f"第 {row['index']} 项 {row['type']}：{row['msg']}")

# ===== 练习题 =====
# 1. 用 as e 捕获 int("abc") 的 ValueError，打印异常类型名和信息两种形式。
# 2. 写函数 log_and_raise(fn)：执行 fn，出错时先打印"记录日志"，再 raise 重新抛出；用 lambda: 1/0 测试并在外层接住。
# 3. 写"错误收集器"类 ErrorCollector：collect(fn) 方法执行函数并记录 (类型, 信息) 到列表；report() 方法打印所有记录；测试 3 个不同错误后输出报告。
