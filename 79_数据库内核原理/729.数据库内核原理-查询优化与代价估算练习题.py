# ===== 第729课：数据库内核原理-查询优化与代价估算 =====
# 知识点：
#   - 逻辑优化：谓词下推、列裁剪、常量折叠、子查询展开、连接重排（等价变换）
#   - 物理优化：为每个逻辑算子选实现（Seq Scan / Index Scan、NL / Hash / Merge Join）
#   - 代价模型：cost ≈ 页 IO × 权重 + CPU 行数；用统计信息估基数 selectivity
#   - 选择率：等值 ≈ 1/NDV，范围用直方图；多条件相乘（独立性假设，常不准）
#   - 连接顺序：n 张表有 n! 种顺序，用动态规划（System R）剪枝
#   - 本课实现小型代价估算器 + 计划对比，演示「为什么优化器选索引」
# 依赖：无（标准库）
import math
from dataclasses import dataclass

N_ROWS = 100_000
PAGE_SIZE = 100          # 每页 100 行 -> 1000 页
N_PAGES = N_ROWS // PAGE_SIZE


@dataclass
class Stats:
    rows: int
    ndv: dict          # 每列不同值个数
    null_frac: dict = None


stats = Stats(N_ROWS, {"id": N_ROWS, "status": 4, "region": 8, "user_id": 5000})


def selectivity(col, op, value, s):
    ndv = s.ndv.get(col, s.rows)
    if op == "=":
        return 1 / ndv
    if op in (">", ">=", "<", "<="):
        return 0.33                  # 经验值；有直方图会更准
    if op == "BETWEEN":
        return 0.1
    if op == "LIKE":
        return 0.05
    return 0.5


def estimate_rows(preds, s):
    sel = 1.0
    for col, op, val in preds:
        sel *= selectivity(col, op, val, s)
    return max(1, int(s.rows * sel))


def seq_scan_cost(s, width=1.0):
    return N_PAGES * 1.0 + s.rows * 0.01 * width


def index_scan_cost(preds, s):
    """B+树：树高约 log_扇出(N)，再加回表读取命中行。"""
    h = math.ceil(math.log(max(s.rows, 2), 100))
    rows = estimate_rows(preds, s)
    # 聚簇索引顺序读，二级索引随机回表更贵
    return h * 1.0 + rows * 0.3


def plan_cost(plan, s, preds):
    rows = estimate_rows(preds, s)
    if plan == "seq_scan + filter":
        return seq_scan_cost(s), rows
    if plan == "index_scan + filter":
        return index_scan_cost(preds, s), rows
    if plan == "seq_scan + filter(pushed)":
        return seq_scan_cost(s), rows
    if plan == "covering_index":
        return index_scan_cost(preds, s) * 0.4, rows    # 无需回表
    raise ValueError(plan)


print("== 统计信息与选择率 ==")
print(f"  表行数={N_ROWS}, 页大小={PAGE_SIZE}, 总页数={N_PAGES}")
print(f"  NDV: {stats.ndv}")
for col, op, val in (("status", "=", "paid"), ("region", "=", 3),
                     ("amount", ">", 100), ("id", "=", 42)):
    print(f"  {col} {op} {val!r:<10} 选择率≈{selectivity(col, op, val, stats):.6f} "
          f"估计行数≈{estimate_rows([(col, op, val)], stats)}")

print("\n== 多条件组合（独立性假设）==")
preds = [("status", "=", "paid"), ("region", "=", 3)]
rows = estimate_rows(preds, stats)
print(f"  两条件相乘 -> 选择率≈{rows/N_ROWS:.6f}, 行数≈{rows}")
print("  实际若 status 与 region 相关，这个估计会明显偏差 -> 需要多列统计/直方图")

print("\n== 单表访问路径代价对比 ==")
for label, p in (("全表扫描 + 过滤", [("status", "=", "paid")]),
                 ("索引扫描 + 过滤", [("status", "=", "paid")]),
                 ("覆盖索引", [("status", "=", "paid")]),
                 ("主键点查", [("id", "=", 42)])):
    plan = {"全表扫描 + 过滤": "seq_scan + filter",
            "索引扫描 + 过滤": "index_scan + filter",
            "覆盖索引": "covering_index",
            "主键点查": "index_scan + filter"}[label]
    cost, est = plan_cost(plan, stats, p)
    print(f"  {label:<16}: 估计输出={est:>6} 行  代价≈{cost:>8.1f}")
print("  高选择率（点查）用索引；低选择率（返回大比例行）全表扫描反而更省")

print("\n== 临界选择率：什么时候索引不再划算 ==")
for sel in (0.0001, 0.001, 0.01, 0.05, 0.1, 0.3, 0.5):
    rows = int(N_ROWS * sel)
    idx = math.ceil(math.log(N_ROWS, 100)) + rows * 0.3
    seq = N_PAGES + N_ROWS * 0.01
    print(f"  返回 {sel:>6.2%} ({rows:>6}行): 索引={idx:>8.1f} 全表={seq:>8.1f} "
          f"-> {'索引' if idx < seq else '全表'}")

print("\n== 连接顺序：动态规划剪枝 ==")
TABLES = {"orders": 100000, "users": 5000, "items": 200, "regions": 8}
def join_card(a, b):
    # 简化：假设按外键连接，输出 ≈ 较大表行数
    return max(TABLES[a], TABLES[b])
def dp_join_order(tables):
    from functools import lru_cache
    names = tuple(sorted(tables))
    @lru_cache(None)
    def best(subset):
        if len(subset) == 1:
            return (TABLES[subset[0]], subset)
        res = None
        # 枚举所有二分划分，取累计中间结果最小的（System R 动态规划思想）
        from itertools import combinations
        k = len(subset)
        for r in range(1, k):
            for left in combinations(subset, r):
                right = tuple(x for x in subset if x not in left)
                c1, o1 = best(tuple(sorted(left)))
                c2, o2 = best(tuple(sorted(right)))
                total = c1 + c2 + join_card(o1[0], o2[0])
                order = o1 + o2
                if res is None or total < res[0]:
                    res = (total, order)
        return res
    return best(names)

cost, order = dp_join_order(TABLES)
print(f"  4 表连接最优顺序: {order}  累计代价≈{cost:,}")
print(f"  全枚举顺序数 = 4! = {math.factorial(4)}；n 表为 n!，必须剪枝")

print("\n== 逻辑优化规则（等价变换）==")
for rule in (
    "  σ(p)(A⋈B) -> σ(p)(A)⋈B        谓词下推（p 只涉及 A）",
    "  π(cols)(σ(p)(R)) -> π(cols)(σ(p)(π(cols∪p.cols)(R)))  列裁剪",
    "  σ(1=0)(R) -> ∅                  常量折叠/矛盾检测",
    "  A⋈B -> B⋈A                      连接交换律（重排基础）",
    "  (A⋈B)⋈C -> A⋈(B⋈C)             结合律（左深树搜索）",
):
    print(" ", rule)

print("\n== 优化器局限 ==")
for line in [
    "  独立性假设在多列相关时低估/高估基数，导致选错计划",
    "  统计信息过期（大量增删改后）会让代价估算失真",
    "  参数化查询的取值不同，通用计划可能不是最优（plan cache 陷阱）",
    "  EXPLAIN ANALYZE 对比「估计行数 vs 实际行数」是排查第一步",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 用等宽直方图估计范围谓词选择率，替代本例的固定 0.33。
# 2. 实现左深树连接枚举，对比与全二分划分的搜索空间大小。
# 3. 给代价模型加入「随机 IO vs 顺序 IO」不同权重，观察临界选择率变化。
# 4. 思考：为什么「返回 30% 行」时全表扫描通常比索引快？
