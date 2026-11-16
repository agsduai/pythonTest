# ===== 第941课：属性测试与模糊测试-Shrinking缩小反例 =====
# 知识点：
#   - 随机找到的反例往往是庞然大物（100 个元素的长列表）—— 难以定位根因
#   - Shrinking：自动把反例「缩小」成仍失败的最简输入
#   - 贪心下降：不断尝试更简单的候选（更短/更接近 0/去掉元素），失败才保留
#   - shrinker 与生成器配对：int 向 0 收、list 去元素/缩元素
#   - 最小反例的价值：人一眼看出 bug 的本质（如「空列表」或「相邻相等」）
# 依赖：无（标准库）
import random
from itertools import islice


def has_bug(value):
    """被测函数的判定（故意藏一个 bug）：列表存在相邻相等元素即失败。"""
    for a, b in zip(value, value[1:]):
        if a == b:
            return True
    return len(value) > 0 and value[0] < 0        # 负数也判失败


def shrink_int(value, test_failed):
    """整数缩小：向 0 方向折半尝试。返回仍失败的最简值。"""
    candidates = [0]
    v = abs(value)
    while v > 0:
        candidates.append(v)
        v //= 2
    if value < 0:
        candidates = [-c for c in candidates]
    current = value
    for candidate in candidates:
        if candidate != current and test_failed(candidate):
            current = candidate
    return current


def shrink_list(value, test_failed):
    """列表缩小：优先删元素，再把每个元素向 0 收。"""
    current = list(value)
    improved = True
    while improved:
        improved = False
        # 1) 尝试删除元素（一段一段删，收敛更快）
        length = len(current)
        chunk = max(1, length // 2)
        while chunk >= 1:
            i = 0
            while i < len(current):
                candidate = current[:i] + current[i + chunk:]
                if candidate and test_failed(candidate):
                    current = candidate
                    improved = True
                else:
                    i += chunk
            chunk //= 2
        # 2) 尝试把每个元素替换成 0
        for i in range(len(current)):
            if current[i] != 0:
                candidate = list(current)
                candidate[i] = 0
                if candidate and test_failed(candidate):
                    current = candidate
                    improved = True
    return current


def find_minimal(generator_draw, shrink_fn, predicate_failed, rng, examples=500):
    """完整流程：随机找反例 -> 缩小到最小。"""
    counterexample = None
    for _ in range(examples):
        value = generator_draw()
        if predicate_failed(value):
            counterexample = value
            break
    if counterexample is None:
        return None, None
    minimal = shrink_fn(counterexample, predicate_failed)
    return counterexample, minimal


print("== 被测判定（藏 bug）与随机搜索 ==")
rng = random.Random(141)


def random_list():
    length = rng.randint(0, 40)
    return [rng.randint(-10, 10) for _ in range(length)]


counterexample, minimal = find_minimal(random_list, shrink_list, has_bug, rng)
if counterexample is not None:
    print(f"  随机反例（长度 {len(counterexample)}）: "
          f"{counterexample[:15]}{'...' if len(counterexample) > 15 else ''}")
    print(f"  缩小后（长度 {len(minimal)}）: {minimal}")
    print(f"  最小反例仍触发 bug: {has_bug(minimal)}")
    print("  一眼可见：bug 的本质是『相邻相等』或『负数』—— 缩小把噪声剥掉了")
else:
    print("  未找到反例（不应发生，判定函数必在负数首元素时失败）")

print("\n== 缩小过程演示（逐步）==")
ce = [5, -3, 7, -2, 9, 4, 1, 8, 6, 2, 0, -7, 3]
print(f"  初始反例: {ce} (长度 {len(ce)})")
step = 0
current = list(ce)
improved = True
while improved:
    improved = False
    length = len(current)
    chunk = max(1, length // 2)
    while chunk >= 1:
        i = 0
        while i < len(current):
            candidate = current[:i] + current[i + chunk:]
            if candidate and has_bug(candidate):
                current = candidate
                improved = True
                step += 1
                print(f"  第{step}步删段(size {chunk}): {current} (长度 {len(current)})")
            else:
                i += chunk
        chunk //= 2
    for i in range(len(current)):
        if current[i] != 0:
            candidate = list(current)
            candidate[i] = 0
            if candidate and has_bug(candidate):
                current = candidate
                improved = True
                step += 1
                print(f"  第{step}步置零: {current}")
print(f"  最终最小反例: {current}")

print("\n== 不同 bug 会有不同的最小反例 ==")
def bug_only_negative(value):
    return len(value) > 0 and any(v < 0 for v in value)


def bug_sum_exceeds(value):
    return sum(value) > 20


ce2, min2 = find_minimal(random_list, shrink_list, bug_only_negative, rng)
ce3, min3 = find_minimal(random_list, shrink_list, bug_sum_exceeds, rng)
print(f"  bug=『含负数』的最小反例:   {min2}")
print(f"  bug=『和超过 20』的最小反例: {min3} (和={sum(min3)})")
print("  同一个 shrinker 服务不同 bug：最小反例自动指向 bug 的本质")

print("\n== 整数单独缩小的过程 ==")
value = -87
print(f"  缩小 {value}:")
candidates = [0]
v = abs(value)
while v > 0:
    candidates.append(v)
    v //= 2
if value < 0:
    candidates = [-c for c in candidates]
print(f"  候选序列（向 0 折半）: {candidates}")
print("  候选按『简化程度』排序：0 最简单，其次大步长折半")

print("\n== Hypothesis 的真实机制 ==")
for line in (
    "  Hypothesis 用「结构化选择序列」驱动生成，缩小是对选择序列的搜索",
    "  好处：任何复合数据都能沿配方缩小（而非仅列表）",
    "  缩小带缓存与去重：同一候选不重复测",
    "  本课的贪心法覆盖 90% 场景；完备最小化是 NP 难的，够用即可",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  Shrinking = 在反例空间里做『保失败的贪心下降』",
    "  删段优先、置零兜底：优先减小结构，再简化内容",
    "  最小反例的价值是把『找 bug』升级为『理解 bug』",
    "  942 课：去哪里找性质 —— 一套现成的性质模式库",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 为字符串实现 shrinker（删字符 → 每个字符变 'a'），对「含大写字母」的
#    判定缩小反例。
# 2. 实现元组 shrinker：两个分量分别缩小（组合 shrinker）。
# 3. 给缩小过程加「尝试次数上限」，对比有/无上限的最小反例质量。
# 4. 思考：为什么贪心缩小可能得不到全局最小反例？举例说明局部最优陷阱。
