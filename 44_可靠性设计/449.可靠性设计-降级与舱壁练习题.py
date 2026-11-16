# ===== 第449课：可靠性设计-降级与舱壁 =====
# 知识点：
#   - 降级（Fallback）：主逻辑失败时返回“次优但可用”的结果（缓存/默认值）
#   - 降级不是吞异常：要记录日志、指标，并明确告知调用方“这是降级结果”
#   - 舱壁（Bulkhead）：按依赖划分资源池，一个依赖拖慢不耗尽全部线程
#   - 反例：所有依赖共用一个线程池 → 慢查询拖垮整个服务
#   - 与第445课熔断、第446课限流共同构成“稳定性三件套”
import time
from concurrent.futures import ThreadPoolExecutor
from functools import wraps


# ---------------- 1. 降级：失败返回缓存/默认值 ----------------
def with_fallback(fallback_value=None, cache=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if cache is not None:
                    cache["value"] = result        # 成功时更新缓存
                return result
            except Exception as exc:
                if cache is not None and "value" in cache:
                    print(f"  [降级] {func.__name__} 失败，返回缓存：{exc}")
                    return cache["value"]
                print(f"  [降级] {func.__name__} 失败，返回默认值：{exc}")
                return fallback_value
        return wrapper
    return decorator


cache = {}


@with_fallback(fallback_value="推荐服务暂不可用", cache=cache)
def recommend(user):
    if user == "fail":
        raise ConnectionError("推荐服务超时")
    return f"给 {user} 的推荐列表"


print("== 降级演示 ==")
print("  正常：", recommend("小明"))
print("  故障：", recommend("fail"))
print("  再次故障（命中缓存）：", recommend("fail"))

# ---- 降级策略要有层级 ----
print("\n== 降级层级 ==")
for item in [
    "L1：返回缓存（最接近真实）",
    "L2：返回默认内容/空列表（保证页面能打开）",
    "L3：关闭非核心功能（如推荐、评论），保住下单主链路",
    "L4：静态兜底页（依赖全挂时）",
]:
    print("  -", item)


# ---------------- 2. 舱壁：按依赖隔离线程池 ----------------
class SlowDependency:
    def __init__(self, delay):
        self.delay = delay
        self.calls = 0

    def query(self):
        self.calls += 1
        time.sleep(self.delay)
        return f"slow-ok（调用 {self.calls} 次）"


class FastDependency:
    def __init__(self):
        self.calls = 0

    def query(self):
        self.calls += 1
        time.sleep(0.01)
        return f"fast-ok（调用 {self.calls} 次）"


print("\n== 舱壁：慢依赖不拖垮快依赖 ==")
slow = SlowDependency(0.3)
fast = FastDependency()

slow_pool = ThreadPoolExecutor(max_workers=2)      # 慢依赖专属池
fast_pool = ThreadPoolExecutor(max_workers=2)      # 快依赖专属池

# 先占满慢依赖池
slow_futures = [slow_pool.submit(slow.query) for _ in range(2)]

start = time.perf_counter()
fast_future = fast_pool.submit(fast.query)
fast_result = fast_future.result(timeout=0.2)
fast_cost = time.perf_counter() - start
print(f"  慢依赖已被占满时，快依赖仍可用：{fast_result}（{fast_cost:.3f}s）")

start = time.perf_counter()
try:
    slow_futures[0].result(timeout=0.05)
except TimeoutError:
    print(f"  慢依赖请求超时（{time.perf_counter() - start:.3f}s），但只影响它自己的池")

# 对照：共用一个大池，慢任务会挤占快任务（这里用 1 个 worker 模拟）
print("\n== 反例：共用一个池（max_workers=1）==")
shared_pool = ThreadPoolExecutor(max_workers=1)
shared_pool.submit(slow.query)
start = time.perf_counter()
try:
    shared_pool.submit(fast.query).result(timeout=0.1)
except TimeoutError:
    print(f"  快依赖被慢任务堵住，{time.perf_counter() - start:.3f}s 内拿不到结果")

slow_pool.shutdown(wait=False, cancel_futures=True)
fast_pool.shutdown(wait=False, cancel_futures=True)
shared_pool.shutdown(wait=False, cancel_futures=True)

# ---- 线程池大小怎么定 ----
print("\n== 资源池设计 ==")
for item in [
    "按依赖分区：数据库、缓存、第三方 API 各一个池",
    "每个池设置上限 + 队列长度上限（第446课限流）",
    "池满时快速失败/降级，而不是无限排队",
    "核心链路与非核心链路分开（下单 vs 推荐）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给 with_fallback 增加“降级回调”，把降级事件写入日志/指标。
# 2. 实现一个 PoolRegistry：按依赖名获取独立线程池。
# 3. 给慢依赖加熔断（第445课），熔断后直接走降级。
# 4. 思考：降级返回值与正常返回值如何区分，避免调用方误判？
