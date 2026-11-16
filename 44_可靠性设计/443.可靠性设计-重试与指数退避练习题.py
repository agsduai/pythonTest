# ===== 第443课：可靠性设计-重试与指数退避 =====
# 知识点：
#   - 重试：应对“临时性故障”（网络抖动、限流、锁冲突），不是万能药
#   - 只重试可恢复错误：ConnectionError/Timeout/5xx；参数错误重试一万次也没用
#   - 指数退避：delay = base × 2^(n-1)，避免雪崩式重试压垮对方
#   - 抖动 jitter：在退避上加随机量，打散大量客户端的重试时刻
#   - 最大次数/最大延迟必须设上限；重试要有日志，方便定位
import random
import time
from functools import wraps


class TransientError(Exception):
    pass


class PermanentError(Exception):
    pass


def retry(max_attempts=3, base_delay=0.1, max_delay=1.0,
          retry_on=(TransientError,), jitter=0.05):
    """带指数退避与抖动的重试装饰器。"""
    if max_attempts < 1:
        raise ValueError("max_attempts 必须 >= 1")

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retry_on as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        print(f"  [{func.__name__}] 第 {attempt} 次失败，放弃")
                        break
                    delay = min(max_delay, base_delay * 2 ** (attempt - 1))
                    delay += random.uniform(0, jitter)
                    print(f"  [{func.__name__}] 第 {attempt} 次失败：{exc}，"
                          f"{delay:.2f}s 后重试")
                    time.sleep(delay)
            raise last_exc

        return wrapper
    return decorator


# ---- 演示 1：前两次临时失败，第三次成功 ----
calls = {"n": 0}


@retry(max_attempts=3, base_delay=0.05)
def flaky_api():
    calls["n"] += 1
    if calls["n"] < 3:
        raise TransientError(f"模拟网络抖动（第 {calls['n']} 次）")
    return f"成功（共调用 {calls['n']} 次）"


print("== 临时故障自动恢复 ==")
print("  结果：", flaky_api())

# ---- 演示 2：永久错误不重试 ----
print("\n== 参数错误不重试 ==")


@retry(max_attempts=5, base_delay=0.05, retry_on=(TransientError,))
def bad_request():
    raise PermanentError("缺少必填参数")


try:
    bad_request()
except PermanentError as exc:
    print("  立刻抛出，没有重试：", exc)

# ---- 演示 3：超过次数后抛出最后一次异常 ----
print("\n== 一直失败 ==")


@retry(max_attempts=3, base_delay=0.02)
def always_fail():
    raise TransientError("服务不可用")


try:
    always_fail()
except TransientError as exc:
    print("  最终失败：", exc)

# ---- 退避时间表 ----
print("\n== 指数退避时间表（base=0.1, max=1.0）==")
for attempt in range(1, 8):
    delay = min(1.0, 0.1 * 2 ** (attempt - 1))
    print(f"  第 {attempt} 次重试前等待 {delay:.2f}s")

# ---- 只读操作才适合自动重试 ----
print("\n== 适用边界 ==")
for item in [
    "适合重试：GET 请求、幂等写入、获取锁、连接建立",
    "不能直接重试：支付扣款、下单创建（除非有幂等键，第447课）",
    "重试风暴：所有客户端同时重试会压垮服务 → 必须加 jitter",
    "与熔断配合：连续失败应先熔断，而不是无限重试（第445课）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给 retry 增加 on_retry 回调，把每次失败写进日志。
# 2. 实现“重试预算”：同一请求总耗时超过 5 秒就放弃。
# 3. 把 retry 用在第410课的 HTTP 客户端请求上。
# 4. 思考：为什么说“重试是放大器”？下游故障时它如何让情况更糟？
