# ===== 第728课：数据库内核原理-查询执行与算子 =====
# 知识点：
#   - 查询计划是一棵算子树：Scan -> Filter -> Project -> Join -> Aggregate -> Sort
#   - 火山模型 Volcano / 迭代器：每个算子实现 open/next/close，逐行拉取（pull）
#   - 物化模型：算子一次产出全部结果，适合排序/哈希连接等阻塞算子
#   - 谓词下推：把 Filter 尽量推到 Scan 附近，减少中间行数
#   - 连接算法：嵌套循环 / 哈希连接 / 排序归并连接，代价差异巨大
#   - 本课用「生成器」实现火山模型，天然惰性、内存 O(1)
# 依赖：无（标准库）
import time

ROWS = 2000
orders = [{"id": i, "user_id": i % 100, "amount": (i * 7) % 500,
           "status": "paid" if i % 3 else "pending", "region": i % 5}
          for i in range(ROWS)]
users = [{"user_id": u, "name": f"u{u}", "vip": u % 7 == 0}
         for u in range(100)]


# ---- 火山模型：每个算子是「输入行迭代器 -> 输出行迭代器」 ----
def scan(rows):
    for r in rows:
        yield r

def filter_op(child, pred):
    for r in child:
        if pred(r):
            yield r

def project_op(child, cols):
    for r in child:
        yield {c: r[c] for c in cols}

def map_op(child, fn):
    for r in child:
        yield fn(r)

def limit_op(child, n):
    for i, r in enumerate(child):
        if i >= n:
            break
        yield r


def hash_join(left, right, left_key, right_key):
    """右表建哈希表，左表逐行探测；O(n+m)。"""
    idx = {}
    for r in right:
        idx.setdefault(r[right_key], []).append(r)
    for l in left:
        for r in idx.get(l[left_key], ()):
            yield {**l, **r}


def nested_loop_join(left, right, left_key, right_key):
    """O(n*m) 教学对照；右表需可重复迭代（本例用 list）。"""
    right = list(right)
    for l in left:
        for r in right:
            if l[left_key] == r[right_key]:
                yield {**l, **r}


def sort_op(child, key, reverse=True):
    yield from sorted(child, key=lambda r: r[key], reverse=reverse)


print("== 执行计划：SELECT o.id, o.amount FROM orders WHERE status='paid' LIMIT 5 ==")
plan = limit_op(
    project_op(
        filter_op(scan(orders), lambda r: r["status"] == "paid"),
        ["id", "amount"]), 5)
print("  ", list(plan))

print("\n== 火山模型是惰性的 ==")
counter = {"n": 0}
def counted_scan():
    for r in orders:
        counter["n"] += 1
        yield r
lazy = limit_op(filter_op(counted_scan(), lambda r: r["amount"] > 490), 3)
print(f"  构造计划后 scan 调用次数 = {counter['n']}（还没拉数据）")
out = list(lazy)
print(f"  取 3 行后 = {counter['n']}（只扫到够用为止，未全表扫描）")
print("  结果:", out)

print("\n== 谓词下推：先过滤再连接 ==")
paid = list(filter_op(scan(orders), lambda r: r["status"] == "paid"))
print(f"  原始 orders={len(orders)}，status='paid' 过滤后={len(paid)}")
print(f"  下推后参与连接的行数减少 {1 - len(paid)/len(orders):.0%}")
pushed = limit_op(hash_join(scan(paid), users, "user_id", "user_id"), 3)
print("  下推后连接样例:", list(pushed))

print("\n== 连接算法对比：哈希 vs 嵌套循环 ==")
t0 = time.perf_counter()
hj = list(hash_join(scan(orders), users, "user_id", "user_id"))
t_hj = time.perf_counter() - t0
t0 = time.perf_counter()
nl = list(nested_loop_join(scan(orders), users, "user_id", "user_id"))
t_nl = time.perf_counter() - t0
print(f"  哈希连接    : {len(hj)} 行, {t_hj*1000:.1f} ms")
print(f"  嵌套循环连接: {len(nl)} 行, {t_nl*1000:.1f} ms, 慢 {t_nl/t_hj:.0f}×")
print("  哈希连接 O(n+m)，嵌套循环 O(n·m)；小表建哈希是常规选择")

print("\n== 聚合与排序（阻塞算子须物化）==")
def avg(xs):
    return sum(xs) / len(xs)
def group_multi(child, key, specs):
    """specs: [(输出名, 输入列, 聚合函数)]，可对不同列做多个聚合。"""
    groups = {}
    for r in child:
        k = r[key]
        groups.setdefault(k, {name: [] for name, _, _ in specs})
        for name, col, _ in specs:
            groups[k][name].append(r[col])
    for k, vals in sorted(groups.items()):
        yield {key: k, **{name: fn(vals[name]) for name, _, fn in specs}}

agg2 = group_multi(filter_op(scan(orders), lambda r: r["status"] == "paid"),
                   "region", [("total", "amount", sum), ("avg", "amount", avg)])
print("  按 region 聚合 paid 订单:")
for r in agg2:
    print("   ", r)
top = limit_op(sort_op(scan(paid), "amount"), 5)
print("  amount Top5:", [r["amount"] for r in top])

print("\n== 算子分类 ==")
for line in (
    "  流式(非阻塞): Scan / Filter / Project / Limit / 嵌套循环左表",
    "  阻塞(需物化): Sort / HashAgg / HashJoin 的 build 阶段",
    "  阻塞算子要内存预算，超了要 spill 到磁盘（external sort）",
    "  火山模型逐行调用开销大，现代引擎用向量化/编译执行优化",
):
    print(" ", line)

print("\n== 执行计划文本 ==")
for line in (
    "  Limit 5",
    "    -> Project (id, amount)",
    "      -> Hash Join (user_id)",
    "        -> Filter (status = 'paid')  [谓词已下推]",
    "          -> Seq Scan orders",
    "        -> Hash (Seq Scan users)",
):
    print(line)

print("\n== 工程要点 ==")
for line in [
    "  EXPLAIN / EXPLAIN ANALYZE 看真实计划与每行基数估计",
    "  统计信息不准会导致选错连接顺序或索引，需 ANALYZE 更新",
    "  生成器实现火山模型很直观，但生产要考虑零拷贝与批处理",
    "  谓词下推、列裁剪、常量折叠属于逻辑优化（第729课）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现排序归并连接，对比三种连接算法在不同数据分布下的耗时。
# 2. 给算子加「行数统计」，输出 EXPLAIN ANALYZE 风格的真实基数。
# 3. 实现 LIMIT 的下推优化，证明能提前终止底层扫描。
# 4. 思考：为什么 Sort / HashAgg 无法做到真正的流式输出？
