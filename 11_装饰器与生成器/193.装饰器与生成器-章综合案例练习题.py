# ===== 第193课：装饰器与生成器-章综合案例 =====
# 知识点：
#   - 综合运用：装饰器增强函数 + 生成器流式数据 + 上下文管理器管资源
#   - 场景：模拟成绩批量统计并写报告
#   - 三者分工：装饰器管“附加行为”，生成器管“数据流动”，with 管“开关”

import os
import random
import time
from contextlib import contextmanager
from functools import wraps


# ---- 装饰器：统计函数耗时 ----
def timer(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"[{func.__name__}] 耗时 {time.perf_counter() - start:.4f} 秒")
        return result

    return wrapper


# ---- 生成器：流式产出数据 ----
def gen_scores(count):
    """产出 count 个 60~100 的随机分数。"""
    for _ in range(count):
        yield random.randint(60, 100)


def to_grade(scores):
    """把分数流转换成等级流。"""
    for score in scores:
        if score >= 90:
            yield "优秀"
        elif score >= 80:
            yield "良好"
        elif score >= 70:
            yield "中等"
        else:
            yield "及格"


# ---- 上下文管理器：报告文件的开与关 ----
@contextmanager
def report_writer(path):
    f = open(path, "w", encoding="utf-8")
    try:
        yield f
    finally:
        f.close()
        print(f"报告已保存：{path}")


@timer
def make_report(path, total=10_000):
    """统计各等级人数并写入报告。"""
    counter = {}
    for level in to_grade(gen_scores(total)):     # 生成器管道
        counter[level] = counter.get(level, 0) + 1
    with report_writer(path) as f:                # 上下文管理器
        for level, n in sorted(counter.items(), key=lambda kv: -kv[1]):
            f.write(f"{level}: {n}\n")
    return counter


result = make_report("score_report_193.txt")
print(result)

os.remove("score_report_193.txt")    # 清理演示文件

# ===== 练习题 =====
# 1. 给 gen_scores 增加 low/high 参数，让 make_report 支持自定义分数区间。
# 2. 编写装饰器 log_args，把 make_report 收到的参数记录下来，与 timer 叠加使用。
# 3. 把 report_writer 改写成类实现（__enter__/__exit__）。
# 4. 思考：如果要统计 1 亿条成绩，这份代码哪里可能出问题？生成器帮了什么忙？
