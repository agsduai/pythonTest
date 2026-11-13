# ===== 第275课：性能优化-综合案例-优化统计程序 =====
# 知识点：
#   - 综合运用：cProfile 定位热点（第271课）→ 数据结构选型（第272课）→ 重写
#   - 场景：统计 5 万条订单中每个用户的消费总额
#   - 反面教材：内层“全用户扫描”制造 O(n×m)；正确姿势：defaultdict 一遍过

import time
from collections import defaultdict


def make_orders(n=50_000):
    import random
    random.seed(7)
    users = [f"user{i}" for i in range(50)]
    return [(random.choice(users), random.randint(1, 100)) for _ in range(n)]


def total_slow(orders, users):
    """反面教材：每笔订单都在用户列表里找一遍。"""
    result = {u: 0 for u in users}
    for user, amount in orders:
        for u in users:                # O(m) 的内层扫描
            if u == user:
                result[u] += amount
    return result


def total_fast(orders):
    """正确姿势：defaultdict 一遍累加。"""
    result = defaultdict(int)
    for user, amount in orders:
        result[user] += amount         # O(1)
    return dict(result)


orders = make_orders()
users = sorted({u for u, _ in orders})

start = time.perf_counter()
slow_result = total_slow(orders, users)
t_slow = time.perf_counter() - start

start = time.perf_counter()
fast_result = total_fast(orders)
t_fast = time.perf_counter() - start

print(f"慢版：{t_slow:.3f} 秒 | 快版：{t_fast:.5f} 秒")
print(f"加速约 {t_slow / max(t_fast, 1e-9):.0f} 倍")
print("结果一致：", slow_result == fast_result)
top3 = sorted(fast_result.items(), key=lambda kv: -kv[1])[:3]
print("消费 Top3：", top3)

# 优化复盘：
#   1) cProfile 会显示 total_slow 的内层循环占 90%+ 时间
#   2) 洞察：内层扫描只是“按键取值” —— dict 本来就是干这个的
#   3) 重写后复杂度 O(n×m) → O(n)，收益来自算法而非抠语法

# ===== 练习题 =====
# 1. 用 cProfile 剖析 total_slow，确认热点在内层循环。
# 2. 把用户数改成 500，观察慢版耗时的增长趋势。
# 3. 继续升级：统计“每个用户最近一次消费时间”（提示：datetime + defaultdict）。
# 4. 思考：如果订单数据大到内存装不下，怎么改造快版？（提示：第191课流式）
