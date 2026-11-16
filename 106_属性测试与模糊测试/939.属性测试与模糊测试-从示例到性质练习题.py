# ===== 第939课：属性测试与模糊测试-从示例到性质 =====
# 知识点：
#   - 示例测试：「我想到这几个输入」；属性测试：「对所有生成的输入，应满足…」
#   - 属性（property）= 谓词 + 随机数据生成器 —— 测试的覆盖面由数据说话
#   - 最经典的性质：roundtrip（编码→解码回到原值）
#   - 随机输入能找到示例测试想不到的边界：负数/空/Unicode/极端长度
#   - 本课用 60 行实现一个迷你属性测试框架，后续课程逐步增强
# 依赖：无（标准库）
import random
from itertools import islice


def encode_int(value):
    """示例被测函数：整数 -> 文本编码（故意保留一个 bug）。"""
    if value == 0:
        return "0"
    sign = "-" if value < 0 else ""
    value = abs(value)
    chunks = []
    while value:
        chunks.append(chr(ord("a") + value % 26))
        value //= 26
    return sign + "".join(reversed(chunks))


def decode_int(text):
    sign = -1 if text.startswith("-") else 1
    body = text.lstrip("-")
    value = 0
    for ch in body:
        value = value * 26 + (ord(ch) - ord("a"))
    return sign * value


def ints_with_boundary(rng, lo=-500, hi=500):
    """带边界注入的整数生成器：30% 概率吐边界值（标准技巧）。"""
    special = [0, 1, -1, lo, hi, 25, 26, 27, -25, -26, -27]
    while True:
        if rng.random() < 0.3:
            yield rng.choice(special)
        else:
            yield rng.randint(lo, hi)


def run_property(generator, property_fn, examples=500):
    """迷你属性测试运行器：生成数据 -> 断言性质 -> 收集失败样本。"""
    failures = []
    for value in islice(generator, examples):
        try:
            if not property_fn(value):
                failures.append((value, "性质返回 False"))
        except Exception as exc:
            failures.append((value, f"{type(exc).__name__}: {exc}"))
        if len(failures) >= 5:
            break
    return failures


def property_roundtrip(value):
    """性质：decode(encode(v)) == v 对所有整数成立。"""
    return decode_int(encode_int(value)) == value


def property_nonempty(value):
    """性质：encode(0 除外) 的结果非空且不带前导零。"""
    encoded = encode_int(value)
    if value == 0:
        return encoded == "0"
    return len(encoded) > 0 and (len(encoded) == 1 or encoded.lstrip("-")[0] != "a")


rng = random.Random(139)

print("== 被测函数与示例测试 ==")
for v in (0, 5, 25, 26, -1, 100):
    enc = encode_int(v)
    dec = decode_int(enc)
    print(f"  encode({v:>4}) = {enc!r:<8} decode -> {dec:>4}  "
          f"{'✓' if dec == v else '✗'}")
print("  示例测试全过 —— 但 bug 藏在示例没覆盖的地方")

print("\n== 示例测试容易漏的边界 ==")
edge = [-26, -27, 676, 703]
for v in edge:
    enc = encode_int(v)
    dec = decode_int(enc)
    print(f"  encode({v:>5}) = {enc!r:<8} decode -> {dec:>5}  "
          f"{'✓' if dec == v else '✗ BUG'}")
print("  值 26 编码为 'ba'？试试就知道：", encode_int(26))

print("\n== 属性测试登场：500 个随机整数（含边界注入）==")
gen = ints_with_boundary(rng, -500, 500)
failures = run_property(gen, property_roundtrip, examples=500)
if failures:
    for value, reason in failures[:5]:
        print(f"  ✗ 输入 {value}: {reason}")
    print(f"  属性测试找到了示例测试漏掉的 bug！（{len(failures)} 个失败样本）")
else:
    print("  未发现失败")
print("  真正的 bug：encode(0) 返回 '0'，但 decode 只认 a..z 字母，")
print("  '0' 被当作非法字符解出 -49 —— 编解码字母表不一致，示例测试没抓到")

print("\n== 第二个性质：编码格式 ==")
failures2 = run_property(ints_with_boundary(rng, -500, 500),
                         property_nonempty, examples=500)
for value, reason in failures2[:5]:
    print(f"  ✗ 输入 {value}: {reason}")
if not failures2:
    print("  格式性质通过 —— 不同性质抓不同类别的 bug")
print("  一组数据可以对应多条性质 —— 每条性质是一个『不变式』")

print("\n== 属性测试 vs 示例测试 ==")
print(f"  {'维度':<14}{'示例测试':<24}{'属性测试'}")
for row in (("数据来源", "人手写（有限个）", "生成器（无限流）"),
            ("覆盖能力", "想多全测多全", "随机探索意想不到的组合"),
            ("失败输出", "哪个断言失败", "带具体反例数据"),
            ("适用场景", "边界明确的功能", "有数学性质的功能")):
    print(f"  {row[0]:<14}{row[1]:<24}{row[2]}")
print("  两者互补：属性测试找 bug，示例测试把找到的 bug 固化成回归用例")

print("\n== 属性的来源（怎么想出性质）==")


def demo_properties():
    for line in (
        "  roundtrip：encode/decode、serialize/parse、compress/decompress",
        "  不变量：排序后长度不变、过滤后是子集",
        "  幂等：sort(sort(x)) == sort(x)、abs(abs(x)) == abs(x)",
        "  数学律：reverse(reverse(x)) == x、a+b == b+a",
        "  对比实现：快速实现 vs 朴素正确实现（942 课）",
    ):
        print("    -", line)


demo_properties()

print("\n== 小结 ==")
for line in (
    "  属性测试 = 生成器 + 谓词 + 自动反例收集，60 行就能起步",
    "  『示例全过』≠ 正确 —— 覆盖面的差距就是 bug 的藏身处",
    "  反例是属性测试最有价值的产出：具体输入 + 具体失败原因",
    "  940 课：把生成器做成可组合的系统（Hypothesis 的核心）",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 修复 encode_int（每 26 进位用两位字符或分隔符），并重跑性质验证通过。
# 2. 为 reverse 实现三条性质：长度不变、reverse(reverse(x))==x、reverse 后
#    元素多重集合相同。
# 3. 把 run_property 的失败样本转成示例测试代码字符串（固化回归用例）。
# 4. 思考：为什么 roundtrip 性质对『有损压缩』不成立？性质必须与函数的
#    契约严格对应。
