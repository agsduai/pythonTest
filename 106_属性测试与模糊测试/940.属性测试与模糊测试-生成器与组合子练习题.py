# ===== 第940课：属性测试与模糊测试-生成器与组合子 =====
# 知识点：
#   - 生成器系统：不可变的数据「配方」—— map/filter/复合/递归
#   - size 参数控制规模：字符串长度、嵌套深度 —— 防止生成器爆炸
#   - 组合子：int()/text()/lists()/one_of() 像积木一样拼出新类型
#   - 递归生成器：JSON/树等自引用结构的关键（深度递减保证终止）
#   - 可复现：生成器由 rng 种子驱动 → 同 seed 同数据（945 课详述）
# 依赖：无（标准库）
import random
import string


class Generator:
    """不可变生成配方：本质是 (rng, size) -> 值 的函数封装。"""

    def __init__(self, draw_fn):
        self._draw = draw_fn

    def generate(self, rng, size=5):
        return self._draw(rng, size)

    def map(self, fn):
        def draw(rng, size):
            return fn(self._draw(rng, size))
        return Generator(draw)

    def filter(self, predicate, max_tries=50):
        def draw(rng, size):
            for _ in range(max_tries):
                value = self._draw(rng, size)
                if predicate(value):
                    return value
            return self._draw(rng, size)          # 兜底（保证不卡死）
        return Generator(draw)

    def flat_map(self, fn):
        def draw(rng, size):
            sub = fn(self._draw(rng, size))
            return sub._draw(rng, size)
        return Generator(draw)


def integers(lo=0, hi=100):
    def draw(rng, size):
        span = max(1, int((hi - lo) * min(size, 10) / 10))
        mid = (lo + hi) // 2
        return max(lo, min(hi, mid + rng.randint(-span, span)))
    return Generator(draw)


def booleans():
    return Generator(lambda rng, size: rng.random() < 0.5)


def texts(charset=string.printable[:62], max_len=20):
    def draw(rng, size):
        length = rng.randint(0, max(0, min(max_len, size * 3)))
        return "".join(rng.choice(charset) for _ in range(length))
    return Generator(draw)


def lists(element_gen, max_len=8):
    def draw(rng, size):
        length = rng.randint(0, max(0, min(max_len, size)))
        return [element_gen.generate(rng, size - 1) for _ in range(length)]
    return Generator(draw)


def one_of(*generators):
    def draw(rng, size):
        return rng.choice(generators).generate(rng, size)
    return Generator(draw)


def tuples(*generators):
    def draw(rng, size):
        return tuple(g.generate(rng, max(1, size - 1)) for g in generators)
    return Generator(draw)


def fixed_dictionaries(mapping):
    def draw(rng, size):
        return {k: g.generate(rng, max(1, size - 1)) for k, g in mapping.items()}
    return Generator(draw)


def recursive(base_gen, expand_fn, max_depth=3):
    """递归生成器：深度递减保证终止。"""
    def draw(rng, size):
        if size <= 0 or rng.random() < 0.3:
            return base_gen.generate(rng, 0)
        return expand_fn(
            lambda: Generator(lambda r, s: draw(r, s - 1)).generate(rng, size))
    return Generator(draw)


rng = random.Random(140)

print("== 原子生成器 ==")
gi = integers(-50, 50)
print(f"  integers(-50,50): {[gi.generate(rng, 10) for _ in range(5)]}")
gt = texts()
print(f"  texts(): {[gt.generate(rng, 5) for _ in range(3)]}")
print(f"  booleans(): {[booleans().generate(rng, 5) for _ in range(5)]}")

print("\n== size 参数：规模随深度增长 ==")
print(f"  {'size':>6}{'生成的最大长度样本':>26}")
for size in (1, 3, 5, 10):
    samples = [lists(integers()).generate(rng, size) for _ in range(200)]
    longest = max(len(s) for s in samples)
    print(f"  {size:>6}{longest:>26}")
print("  size 控制生成的『预算』—— 属性测试先小后大找 bug")

print("\n== 组合子拼装 ==")
person_gen = fixed_dictionaries({
    "name": texts(string.ascii_letters, 10),
    "age": integers(1, 99),
    "tags": lists(texts(string.ascii_lowercase, 6), max_len=4),
})
sample = person_gen.generate(rng, 6)
print(f"  person: {sample}")

pairs = tuples(integers(0, 9), texts("abc", 4))
print(f"  tuples: {[pairs.generate(rng, 4) for _ in range(3)]}")

even_ints = integers(0, 100).filter(lambda v: v % 2 == 0)
print(f"  filter 偶数: {[even_ints.generate(rng, 10) for _ in range(5)]}")
negated = integers(0, 100).map(lambda v: -v)
print(f"  map 取负: {[negated.generate(rng, 10) for _ in range(5)]}")

print("\n== one_of 与递归结构 ==")
json_scalar = one_of(integers(-20, 20), texts(string.ascii_letters, 8),
                     booleans())
json_like = recursive(json_scalar,
                      lambda sub: lists(sub, max_len=4), max_depth=3)
for _ in range(3):
    print(f"  json_like: {json_like.generate(rng, 6)}")
print("  递归展开时 size 递减 —— 保证终止的关键")

print("\n== 用生成器驱动属性测试 ==")


def is_valid_person(p):
    return (isinstance(p["name"], str)
            and 1 <= p["age"] <= 99
            and all(isinstance(t, str) for t in p["tags"]))


fail_count = 0
for _ in range(300):
    p = person_gen.generate(rng, 8)
    if not is_valid_person(p):
        fail_count += 1
print(f"  300 个生成样本的性质违规 = {fail_count}")

print("\n== 生成器的不可变组合 ==")
base = lists(integers(0, 9), max_len=3)
derived = base.map(lambda lst: sorted(lst))
sample_base = base.generate(rng, 4)
print(f"  base 生成: {sample_base}")
print(f"  derived 是新配方，不影响 base —— 组合子层层叠加")

print("\n== Hypothesis 对应关系 ==")
print(f"  {'本课':<24}{'Hypothesis'}")
for row in (("integers(lo,hi)", "st.integers()"),
            ("texts(charset)", "st.text(alphabet=)"),
            ("lists(g)", "st.lists()"),
            ("one_of(*gs)", "st.one_of()"),
            ("recursive(...)", "st.recursive()"),
            ("fixed_dictionaries", "st.fixed_dictionaries()")):
    print(f"  {row[0]:<24}{row[1]}")
print("  生成器即策略（strategy）—— 概念完全同构")

print("\n== 小结 ==")
for line in (
    "  生成器 = 数据配方；组合子让配方像积木一样复用",
    "  size 预算控制规模与终止性 —— 递归生成器必须递减",
    "  filter 要有兜底，防止约束过紧卡死",
    "  941 课：失败之后怎么办 —— shrinking 缩小反例",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「带权 one_of」：按频率选择子生成器（如 70% 整数 30% 列表）。
# 2. 实现 UUID 生成器与「日期字符串」生成器（校验合法日期）。
# 3. 让 lists 支持「唯一元素」参数（去重直到成功或超限）。
# 4. 思考：为什么生成器要设计成不可变配方而不是迭代器？组合与复用
#    分别受益于什么？
