# ===== 第944课：属性测试与模糊测试-模糊测试与覆盖率引导 =====
# 知识点：
#   - Fuzzing：喂随机/变异输入给程序，目标不是断言性质而是「不崩溃」
#   - 变异策略：位翻转/截断/替换/拼接 —— 从种子语料进化出深路径输入
#   - 覆盖率引导：命中新代码路径的输入保留进语料 —— 比纯随机挖得深
#   - 崩溃去重：按异常类型+位置签名归类，避免同一 bug 刷屏
#   - 属性测试 vs Fuzzing：前者有模型有断言，后者广撒网找崩溃
# 依赖：无（标准库）
import random
from collections import Counter


def parse_config(text):
    """被测迷你解析器：key=value 行，# 注释；故意藏崩溃点。
    崩溃点 1：值包含 '@' 时越界；崩溃点 2：行首 '\\x00'。"""
    result = {}
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line[0] == "\x00":
            raise ValueError("空字节：未处理的边缘输入")
        key, _, value = line.partition("=")
        if not key:
            continue
        if "@" in value:
            index = value.index("@")
            result[key] = value[index - 3:index + 5]   # 负切片陷阱：可能乱序
        else:
            result[key] = value
    return result


def mutate(text, rng):
    """对输入做一次随机变异。"""
    if not text:
        return rng.choice(["a=1", "\x00", "#c", "=@@", "k=1@2"])
    ops = ("flip", "delete", "insert", "replace", "dup")
    op = rng.choice(ops)
    pos = rng.randrange(len(text))
    if op == "flip":
        ch = rng.choice("@\x00#=ab \n1")
        return text[:pos] + ch + text[pos + 1:]
    if op == "delete":
        return text[:pos] + text[pos + 1:]
    if op == "insert":
        ch = rng.choice("@\x00#=ab \n1")
        return text[:pos] + ch + text[pos:]
    if op == "replace":
        return text[:pos] + rng.choice(["#comment", "k=@@\n", "\x00line"]) + text[pos + 1:]
    return text + "\n" + text                    # dup：拼接扩大


def coverage_key(text):
    """伪覆盖率：解析器各分支的命中签名（用真实插桩太重，教学简化）。"""
    keys = set()
    if "#" in text:
        keys.add("comment")
    if "\x00" in text:
        keys.add("nul")
    if "=" in text:
        keys.add("assign")
    if "@" in text:
        keys.add("at")
    if "\n\n" in text:
        keys.add("blank")
    return frozenset(keys)


def fuzz(target, seeds, rng, rounds=3000, coverage_guided=True):
    """主循环：变异 → 执行 → 捕获崩溃 → 覆盖率引导语料进化。"""
    corpus = list(seeds)
    seen_coverage = set()
    for seed in seeds:
        seen_coverage.add(coverage_key(seed))
    crashes = {}
    for round_i in range(rounds):
        if coverage_guided and corpus:
            base = rng.choice(corpus)
        else:
            base = rng.choice(seeds)
        candidate = mutate(base, rng)
        try:
            target(candidate)
        except ValueError as exc:
            signature = str(exc).split(":")[0]
            crashes.setdefault(signature, candidate)
        except Exception as exc:
            signature = f"{type(exc).__name__}"
            crashes.setdefault(signature, candidate)
        else:
            if coverage_guided:
                cov = coverage_key(candidate)
                if cov and cov not in seen_coverage:
                    seen_coverage.add(cov)
                    corpus.append(candidate)      # 新覆盖 → 加入语料
    return crashes, corpus, seen_coverage


print("== 被测解析器与种子 ==")
seeds = ["a=1", "# comment", "k=v"]
print(f"  种子语料: {seeds}")
print("  已知崩溃点：\\x00 开头的行（ValueError）与 @ 值的负切片行为")

print("\n== 纯随机变异（无覆盖引导）==")
rng = random.Random(144)
crashes_rand, corpus_rand, cov_rand = fuzz(
    parse_config, seeds, random.Random(1), rounds=2000, coverage_guided=False)
print(f"  崩溃签名: {dict(Counter(c[:20] for c in crashes_rand.values()) if False else {k: 1 for k in crashes_rand})}")
print(f"  发现崩溃类别 = {len(crashes_rand)}, 语料 = {len(corpus_rand)}, "
      f"覆盖分支 = {len(cov_rand)}")

print("\n== 覆盖率引导的模糊测试 ==")
crashes_cov, corpus_cov, cov_cov = fuzz(
    parse_config, seeds, random.Random(2), rounds=2000, coverage_guided=True)
print(f"  发现崩溃类别 = {len(crashes_cov)}, 语料 = {len(corpus_cov)}, "
      f"覆盖分支 = {len(cov_cov)}")
print(f"  覆盖分支明细: {sorted(c for s in cov_cov for c in s)}")
print("  覆盖率引导的语料更大、分支覆盖更全 —— 同样的轮数挖得更深")

print("\n== 崩溃去重与复现 ==")
for signature, input_text in crashes_cov.items():
    print(f"  签名 [{signature}] 最短复现输入: {input_text!r}")
    try:
        parse_config(input_text)
        print(f"    -> 未崩溃（签名归类有误）")
    except Exception as exc:
        print(f"    -> 确认崩溃: {type(exc).__name__}: {exc}")
print("  每个崩溃都保存最小触发输入 —— fuzzing 的核心产出物")

print("\n== 修复后回归 ==")
def parse_config_fixed(text):
    result = {}
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        if not key:
            continue
        index = value.find("@")
        if index != -1:
            lo = max(0, index - 3)                # 修复负切片
            result[key] = value[lo:index + 5]
        else:
            result[key] = value
    return result


crash_after = 0
for input_text in crashes_cov.values():
    try:
        parse_config_fixed(input_text)
    except Exception:
        crash_after += 1
print(f"  修复后的解析器对 {len(crashes_cov)} 个崩溃输入的崩溃数 = {crash_after}")
print("  fuzzing 的标准闭环：崩溃 → 修复 → 崩溃输入固化为回归用例")

print("\n== 变异策略的效果对比 ==")
print(f"  {'策略':<14}{'特点'}")
for row in (("位翻转", "翻出非法字符/边界值"),
            ("截断/拼接", "制造超长与畸形结构"),
            ("字典替换", "注入领域关键词（#、\\x00）"),
            ("覆盖率引导", "保留打开新路径的输入")):
    print(f"  {row[0]:<14}{row[1]}")

print("\n== 属性测试 vs 模糊测试 ==")
for line in (
    "  属性测试：有生成器 + 断言性质 + shrinking —— 找『逻辑错误』",
    "  Fuzzing：变异 + 只关心崩溃 —— 找『健壮性缺陷』",
    "  互补：fuzz 发现崩溃输入 → 转成属性测试的边界注入 → 945 课固化",
    "  安全领域几乎只用 fuzzing（AFL/libFuzzer）；正确性领域偏爱属性测试",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  fuzzing = 变异 + 执行 + 崩溃签名归类，300 行内可以自建",
    "  覆盖率引导让同样的轮数覆盖更多分支 —— 语料进化的力量",
    "  每个崩溃输入都要修复后固化为回归用例，否则白测",
    "  945 课：可复现性 —— 随机测试的工程化管理",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现真实覆盖率插桩：用 sys.settrace 统计执行到的行号，替换伪覆盖签名。
# 2. 实现「语料最小化」：删掉对覆盖无贡献的语料项。
# 3. 给 fuzzing 加「时间预算」与「崩溃上限」，模拟 CI 中的运行策略。
# 4. 思考：为什么 fuzzing 很难发现『逻辑错误』（如排序错了但没崩溃）？
