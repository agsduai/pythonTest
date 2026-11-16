# ===== 第945课：属性测试与模糊测试-可复现性与工程化 =====
# 知识点：
#   - 随机测试的命门：『这次失败了我却复现不了』—— 可复现性是工程底线
#   - 方案：失败时记录 seed + 参数 → 同 seed 严格重放
#   - 生成器是确定性的：同种子 + 同调用序列 → 同数据
#   - 失败样本要「固化」为示例回归用例（进 CI 的最小用例集）
#   - CI 策略：默认小样本 + 夜间大样本 + 失败 seed 持久化
# 依赖：无（标准库）
import json
import random
from itertools import islice


def buggy_contains(text, pattern):
    """被测函数：含大小写敏感 bug —— pattern 为空串时行为异常。"""
    if not pattern:
        return True
    return pattern.lower() in text.lower()


def contains_spec(text, pattern):
    """规格（神谕）：空串应视为『不存在』（业务定义）。"""
    if not pattern:
        return False
    return pattern.lower() in text.lower()


def generate_case(rng):
    text = "".join(rng.choice("abAB c") for _ in range(rng.randint(0, 10)))
    pattern = "".join(rng.choice("abAB") for _ in range(rng.randint(0, 3)))
    return {"text": text, "pattern": pattern}


class PropertySession:
    """带 seed 记录与复现的属性测试会话。"""

    def __init__(self, seed):
        self.seed = seed
        self.rng = random.Random(seed)
        self.failures = []

    def run(self, examples=500):
        for i in range(examples):
            case = generate_case(self.rng)
            try:
                if buggy_contains(case["text"], case["pattern"]) != \
                        contains_spec(case["text"], case["pattern"]):
                    self.failures.append({"index": i, "seed": self.seed,
                                          **case})
                    if len(self.failures) >= 5:
                        break
            except Exception as exc:
                self.failures.append({"index": i, "seed": self.seed, **case,
                                      "error": f"{type(exc).__name__}: {exc}"})
                if len(self.failures) >= 5:
                    break
        return self.failures

    def replay(self, failure):
        """用记录的 seed + index 严格重放单个失败。"""
        rng = random.Random(failure["seed"])
        case = None
        for i in range(failure["index"] + 1):
            case = generate_case(rng)
        return case == {k: failure[k] for k in ("text", "pattern")}


print("== 第一次运行：seed=945 发现失败 ==")
session = PropertySession(seed=945)
failures = session.run(examples=500)
print(f"  失败样本 {len(failures)} 个:")
for f in failures:
    desc = (f"text={f['text']!r} pattern={f['pattern']!r}"
            + (f" 错误 {f['error']}" if "error" in f else ""))
    print(f"    #{f['index']} seed={f['seed']}: {desc}")

print("\n== 同 seed 重放：严格一致 ==")
first = failures[0]
replayed_case = session.replay(first)
print(f"  重放 #{first['index']} 得到的输入 = {replayed_case}")
print(f"  与失败记录一致: {replayed_case == {k: first[k] for k in ('text', 'pattern')}}")
print("  rng 是确定性的：同 seed → 同调用序列 → 同数据流")

print("\n== 不同 seed 的失败位置不同 ==")
all_failures = 0
for seed in (945, 946, 947):
    s = PropertySession(seed)
    f = s.run(examples=300)
    all_failures += len(f)
    first_info = f[0] if f else None
    print(f"  seed={seed}: 失败 {len(f)} 个"
          + (f"，首个在 #{first_info['index']}" if first_info else ""))
print(f"  三轮共 {all_failures} 个失败 —— bug 频发但每次位置不同")
print("  失败的『随机位置』正是要记录 seed 的原因")

print("\n== 固化为回归用例 ==")
regression_cases = []
for f in failures:
    case = {"text": f["text"], "pattern": f["pattern"],
            "expect_spec": contains_spec(f["text"], f["pattern"])}
    regression_cases.append(case)
print(f"  固化 {len(regression_cases)} 个用例（JSON 可序列化）:")
for c in regression_cases[:3]:
    print(f"    {json.dumps(c, ensure_ascii=False)}")
print("  每条用例既包含输入也包含期望输出 —— 独立于属性框架可执行")


def run_regression(cases):
    passed = 0
    for case in cases:
        got = buggy_contains(case["text"], case["pattern"])
        passed += (got == case["expect_spec"])
    return passed, len(cases)


passed, total = run_regression(regression_cases)
print(f"  回归运行: {passed}/{total} 通过（bug 未修，失败用例持续报警）")

print("\n== CI 策略 ==")
print(f"  {'阶段':<14}{'样本量':<10}{'种子策略':<20}")
for row in (("每次提交", "100", "CI 时间戳派生"),
            ("夜间任务", "5000", "固定 + 轮换"),
            ("发布前", "20000", "历史失败种子全集")):
    print(f"  {row[0]:<14}{row[1]:<10}{row[2]}")
print("  关键规则：失败时立即保存 seed 与反例 —— 修复前它们是唯一线索")

print("\n== 失败样本的最小化衔接 ==")
print("  固化前先过一遍 941 课的 shrinking：")
first_case = (first["text"], first["pattern"])
print(f"    原始反例: {first_case}")
print("    （缩小流程见 941 课：删字符/化简 → 最小反例 → 固化）")

print("\n== 工程清单 ==")
for line in (
    "  1. 种子与数据流：失败即记录，重放必须严格一致",
    "  2. 回归固化：最小反例 → 示例用例进 CI（与属性测试双轨）",
    "  3. 预算分层：日常快测 + 夜间深测 + 发布前全量",
    "  4. 覆盖对账：统计生成数据命中的分支（944 课覆盖率）",
    "  5. 口径统一：属性、神谕、回归用例三者的期望值来源一致",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  随机测试的生命线是可复现：seed + 调用序列 = 完整档案",
    "  失败样本的去向：最小化 → 固化 → 回归 → 修复后转绿",
    "  属性测试与示例测试在 CI 里形成『探索 + 防御』的双层结构",
    "  946 课：综合案例 —— 给迷你 JSON 解析器配全套测试",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「失败归档文件」：JSONL 追加保存 seed/index/输入，供 CI 下载分析。
# 2. 实现「样本量自适应」：连续 50 轮无失败则加倍样本量，有失败则重置。
# 3. 让 generate_case 支持从历史失败语料中采样（944 课语料进化思想）。
# 4. 思考：为什么『同 seed 重放』要求调用序列也一致？中途插入一次额外
#    的 rng 调用会发生什么？
