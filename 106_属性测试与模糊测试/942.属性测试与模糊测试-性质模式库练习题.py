# ===== 第942课：属性测试与模糊测试-性质模式库 =====
# 知识点：
#   - 写属性测试最难的不是框架，而是「想出性质」—— 本课给一套现成模式
#   - 幂等性 / 往返性 / 不变量 / 神谕对比（oracle）/ 变换可交换
#   - 神谕对比：朴素正确实现 vs 优化实现 —— 优化不许改变行为
#   - 模型对比：用简单模型验证复杂系统（与 943 课状态测试衔接）
#   - 每个模式配一个可运行的验证演示
# 依赖：无（标准库）
import random
from itertools import islice


class PropertyRunner:
    """939 课运行器的增强版：支持多生成器与统计。"""

    def __init__(self, rng):
        self.rng = rng

    def check(self, name, draw_fn, property_fn, examples=300):
        failures = []
        for _ in range(examples):
            value = draw_fn()
            try:
                if not property_fn(value):
                    failures.append(value)
            except Exception as exc:
                failures.append((value, f"{type(exc).__name__}: {exc}"))
            if len(failures) >= 3:
                break
        status = "✓ 通过" if not failures else f"✗ 失败 {len(failures)} 例"
        print(f"  [{name}] {status}")
        for f in failures[:2]:
            print(f"      反例: {f!r}")
        return not failures


rng = random.Random(142)
runner = PropertyRunner(rng)

# ---------- 模式 1：幂等性 ----------
print("== 模式 1：幂等性（f(f(x)) == f(x)）==")
def dedup_consecutive(items):
    out = []
    for x in items:
        if not out or out[-1] != x:
            out.append(x)
    return out


def random_list():
    return [rng.randint(0, 3) for _ in range(rng.randint(0, 15))]


runner.check(
    "dedup_consecutive 幂等",
    random_list,
    lambda xs: dedup_consecutive(dedup_consecutive(xs)) == dedup_consecutive(xs))

# ---------- 模式 2：往返性 ----------
print("\n== 模式 2：往返性（pack/unpack 保持信息）==")
def pack(items):
    """游程编码。"""
    runs = []
    for x in items:
        if runs and runs[-1][0] == x:
            runs[-1] = (x, runs[-1][1] + 1)
        else:
            runs.append((x, 1))
    return runs


def unpack(runs):
    out = []
    for value, count in runs:
        out.extend([value] * count)
    return out


runner.check(
    "unpack(pack(x)) == x",
    random_list,
    lambda xs: unpack(pack(xs)) == xs)

# ---------- 模式 3：不变量 ----------
print("\n== 模式 3：不变量（输出保持输入的关键性质）==")
def sort_by_key(items):
    return sorted(items, key=lambda kv: -kv[1])


def invariant_sorted_desc(items):
    keys = [k for k, _ in items]
    return all(keys[i] >= keys[i + 1] for i in range(len(keys) - 1))


def invariant_same_multiset(before, after):
    return sorted(before) == sorted(after)


def draw_pairs():
    return [(f"item{rng.randint(1, 8)}", rng.randint(0, 9))
            for _ in range(rng.randint(0, 10))]


runner.check(
    "sort_by_key 不变量（降序 + 多重集不变）",
    draw_pairs,
    lambda items: invariant_sorted_desc(sort_by_key(items))
    and invariant_same_multiset(
        [k for k, _ in items], [k for k, _ in sort_by_key(items)]))

# ---------- 模式 4：神谕对比（oracle） ----------
print("\n== 模式 4：神谕对比（优化版 vs 朴素版）==")
def contains_naive(items, target):
    """O(n) 朴素实现 = 神谕。"""
    return target in items


class SortedSet:
    """优化实现：有序列表 + 二分。"""

    def __init__(self):
        self.items = []

    def add(self, value):
        lo, hi = 0, len(self.items)
        while lo < hi:
            mid = (lo + hi) // 2
            if self.items[mid] < value:
                lo = mid + 1
            else:
                hi = mid
        if lo >= len(self.items) or self.items[lo] != value:
            self.items.insert(lo, value)

    def contains(self, value):
        lo, hi = 0, len(self.items)
        while lo < hi:
            mid = (lo + hi) // 2
            if self.items[mid] < value:
                lo = mid + 1
            else:
                hi = mid
        return lo < len(self.items) and self.items[lo] == value


def draw_ops():
    return [(rng.choice(("add", "contains")), rng.randint(0, 9))
            for _ in range(rng.randint(0, 12))]


def oracle_check(ops):
    model = set()
    fast = SortedSet()
    for op, v in ops:
        if op == "add":
            model.add(v)
            fast.add(v)
        else:
            if contains_naive(sorted(model), v) != fast.contains(v):
                return False
    return True


runner.check("SortedSet.contains 神谕对比", draw_ops, oracle_check)

# ---------- 模式 5：变换可交换 ----------
print("\n== 模式 5：变换可交换（两个操作顺序无关）==")
runner.check(
    "upper/lower 不可交换是反例（示范假性质）",
    lambda: rng.choice(["aBc", "AbC", "abc"]),
    lambda s: s.upper().lower() == s.lower().upper())
print("  upper/lower 交换会把 'aBc' 变成 'abc' vs 'ABC' —— 假性质被识破")
print("  教训：『可交换』性质只对真正独立的变换成立，写前先想清楚")

# ---------- 模式 6：关系保持（metamorphic） ----------
print("\n== 模式 6：Metamorphic 关系（输入变换 -> 输出可预测变换）==")
def word_count(text):
    return len(text.split())


runner.check(
    "重复文本后计数不变（重复不产生新词）",
    lambda: " ".join(rng.choice(["hello", "world", "foo", "bar"])
                     for _ in range(rng.randint(0, 10))),
    lambda s: word_count(s + " " + s) == word_count(s) * 2)

print("\n== 模式速查表 ==")
print(f"  {'模式':<16}{'性质形式':<34}{'典型场景'}")
for row in (("幂等", "f(f(x)) == f(x)", "规范化/去重/压缩"),
            ("往返", "decode(encode(x)) == x", "序列化/编码"),
            ("不变量", "输出满足关键约束", "排序/过滤/划分"),
            ("神谕对比", "fast(x) == naive(x)", "性能优化不改行为"),
            ("可交换", "f(g(x)) == g(f(x))", "独立变换"),
            ("Metamorphic", "输入变换→输出可预测", "难以直接断言的输出")):
    print(f"  {row[0]:<16}{row[1]:<34}{row[2]}")

print("\n== 小结 ==")
for line in (
    "  性质模式库把『想性质』变成『查表组合』",
    "  神谕对比是重构的安全网：任何优化都应配一个朴素神谕",
    "  假性质（如 upper/lower 交换）会被测试立刻打脸 —— 这也是价值",
    "  943 课：把性质测试从『单次调用』升级到『命令序列』",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 为「LRU 缓存」写神谕对比测试：朴素 dict+时间戳 vs OrderedDict 实现。
# 2. 为「路径规范化」函数写往返与幂等性质（os.path.normpath）。
# 3. 找出一个你身边函数的 metamorphic 关系并写成属性测试。
# 4. 思考：神谕对比中如果神谕本身有 bug 会怎样？如何降低这种风险
#    （两个独立实现交叉验证）？
