# ===== 第188课：装饰器与生成器-带参数的装饰器 =====
# 知识点：
#   - 带参数的装饰器 = 装饰器工厂，共三层：收参数 → 收函数 → 做包装
#   - 使用时必须“调用”装饰器：@repeat(times=3)
#   - 多个装饰器叠加：自下而上包装，自上而下执行（洋葱结构）
#   - 典型应用：重试、限次、权限校验

import random
import time
from functools import wraps


def repeat(times):
    """让被装饰函数连续执行 times 次的装饰器工厂。"""

    def decorator(func):              # 第二层：接收被装饰的函数

        @wraps(func)
        def wrapper(*args, **kwargs):   # 第三层：真正干活的包装函数
            result = None
            for _ in range(times):
                result = func(*args, **kwargs)
            return result

        return wrapper

    return decorator


@repeat(times=3)
def greet(name):
    print(f"你好，{name}！")
    return name


greet("小明")        # 打印 3 次


# 实用案例：失败自动重试（爬虫、接口调用常用）
def retry(times=3, delay=0.2):
    """执行出错时自动重试，最多 times 次，每次间隔 delay 秒。"""

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    print(f"第 {attempt} 次失败：{type(exc).__name__}: {exc}")
                    if attempt < times:
                        time.sleep(delay)
            raise RuntimeError(f"重试 {times} 次后仍然失败")

        return wrapper

    return decorator


@retry(times=3, delay=0.1)
def flaky_api():
    """模拟不稳定接口：约一半概率抛出网络错误。"""
    if random.random() < 0.5:
        raise ConnectionError("网络抖动")
    return "请求成功"


print(flaky_api())


# 多个装饰器叠加：像洋葱一样层层包裹
def deco_a(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        print("A 前处理")
        result = func(*args, **kwargs)
        print("A 后处理")
        return result

    return wrapper


def deco_b(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        print("B 前处理")
        result = func(*args, **kwargs)
        print("B 后处理")
        return result

    return wrapper


@deco_a          # 后套上的先执行“前处理”
@deco_b
def hello():
    print("hello")


hello()   # 输出顺序：A 前 → B 前 → hello → B 后 → A 后

# ===== 练习题 =====
# 1. 编写带参数的装饰器 count_calls(max_calls)，超过调用次数时
#    抛出 RuntimeError("超过最大调用次数")。
# 2. 给 retry 增加只捕获特定异常的能力：
#    retry(times=3, exceptions=(ConnectionError,))。
# 3. 调换 hello 上方两个装饰器的顺序再运行，验证“洋葱结构”的说法。
# 4. 思考：@repeat(3) 与 @repeat 的区别是什么？后者会发生什么？
