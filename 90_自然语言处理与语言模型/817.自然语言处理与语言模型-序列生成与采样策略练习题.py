# ===== 第817课：自然语言处理与语言模型-序列生成与采样策略 =====
# 知识点：
#   - 生成策略决定「如何从概率分布中选 token」，直接影响文本质量和多样性
#   - greedy：总选概率最高的 token，确定性但可能重复/单调
#   - temperature：logits 除以 T，T<1 更保守、T>1 更随机
#   - top-k：只在概率最高的 k 个 token 里采样
#   - top-p (nucleus)：选累计概率达 p 的最小集合，动态截断
#   - beam search：保留 top-B 个部分序列，适合翻译等「有唯一答案」的任务
#   - 与第73章随机采样呼应：温度采样是「带温度的分布重参数化」
# 依赖：无（标准库）
import math
import random


def softmax(logits, temperature=1.0):
    scaled = [l / temperature for l in logits]
    m = max(scaled)
    exps = [math.exp(x - m) for x in scaled]
    s = sum(exps)
    return [e/s for e in exps]


def sample(probs, rng):
    u = rng.random()
    acc = 0.0
    for i, p in enumerate(probs):
        acc += p
        if u < acc:
            return i
    return len(probs) - 1


def top_k_filter(probs, k):
    """只保留 top-k 个概率，其余置 0 后重新归一化。"""
    ranked = sorted(range(len(probs)), key=lambda i: -probs[i])
    keep = set(ranked[:k])
    filtered = [p if i in keep else 0.0 for i, p in enumerate(probs)]
    s = sum(filtered) or 1.0
    return [p/s for p in filtered]


def top_p_filter(probs, p_threshold=0.9):
    """nucleus：取累计概率达 p 的最小集合。"""
    ranked = sorted(range(len(probs)), key=lambda i: -probs[i])
    keep = set()
    acc = 0.0
    for i in ranked:
        keep.add(i); acc += probs[i]
        if acc >= p_threshold:
            break
    filtered = [p if i in keep else 0.0 for i, p in enumerate(probs)]
    s = sum(filtered) or 1.0
    return [p/s for p in filtered]


def beam_search(probs_per_step, beam_width=3, steps=3):
    """Beam search：保留 top-B 个部分序列，逐步扩展。"""
    beams = [(0.0, [])]      # (log_prob, token_list)
    for step in range(steps):
        candidates = []
        for log_p, tokens in beams:
            probs = probs_per_step(step, tokens)
            for i, p in enumerate(probs):
                if p > 0:
                    candidates.append((log_p + math.log2(p), tokens + [i]))
        beams = sorted(candidates, key=lambda x: -x[0])[:beam_width]
    return beams


print("== 温度采样 ==")
logits = [2.0, 1.5, 1.0, 0.5, 0.0, -0.5]
print(f"  logits: {logits}")
for T in (0.3, 0.5, 1.0, 1.5, 2.0):
    p = softmax(logits, T)
    print(f"  T={T:<4}: {['%.3f' % v for v in p]}")
print("  T<1 更尖锐（保守）；T>1 更平坦（多样）；T→0 变成 argmax")

print("\n== top-k 截断 ==")
probs = softmax(logits, temperature=1.0)
for k in (1, 2, 3, 4):
    f = top_k_filter(probs, k)
    nz = [i for i, p in enumerate(f) if p > 0]
    print(f"  top-{k}: 保留 {nz} -> {['%.3f' % v for v in f]}")
print("  top-k 的问题是 k 固定：分布尖锐时 k 太多、平坦时 k 太少")

print("\n== top-p (nucleus) 截断 ==")
for p_thresh in (0.5, 0.8, 0.9, 0.95):
    f = top_p_filter(probs, p_thresh)
    nz = [i for i, p in enumerate(f) if p > 0]
    print(f"  p={p_thresh}: 保留 {nz} -> {['%.3f' % v for v in f]}")
print("  top-p 自适应：分布尖锐时保留少数，平坦时保留更多")

print("\n== 用 N-gram 模型做生成 ==")
CORPUS = [
    "the cat sat on the mat",
    "the cat ate the fish",
    "the dog sat on the mat",
    "the dog barked at the cat",
    "the bird flew over the cat",
    "a cat sat near the dog",
]
from collections import Counter, defaultdict
model = defaultdict(Counter)
for line in CORPUS:
    toks = line.split()
    for i in range(len(toks)-1):
        model[toks[i]][toks[i+1]] += 1

def generate_with_strategy(model, start, strategy, rng, max_len=12):
    tokens = start.split()
    result = []
    for _ in range(max_len):
        ctx = tokens[-1]
        cands = model.get(ctx)
        if not cands:
            break
        words = list(cands.keys())
        counts = list(cands.values())
        total = sum(counts)
        probs = [c/total for c in counts]
        if strategy == "greedy":
            idx = max(range(len(probs)), key=lambda i: probs[i])
        elif strategy == "temperature":
            idx = sample(softmax([math.log2(p) for p in probs], 1.0), rng)
        elif strategy == "top-p":
            filtered = top_p_filter(probs, 0.9)
            idx = sample(filtered, rng)
        elif strategy == "top-k":
            filtered = top_k_filter(probs, 2)
            idx = sample(filtered, rng)
        else:
            idx = sample(probs, rng)
        word = words[idx]
        if word == "</s>": break
        result.append(word)
        tokens.append(word)
    return " ".join(result)

rng = random.Random(7)
start_word = "the"
for strategy in ("greedy", "temperature", "top-p", "top-k"):
    print(f"  [{strategy}] 生成:")
    for s in range(3):
        text = generate_with_strategy(model, start_word, strategy, rng, max_len=12)
        print(f"    seed={s}: {text}")

print("\n== Beam Search vs Greedy vs Sampling ==")
def probs_step(step, tokens):
    ctx = tokens[-1] if tokens else "the"
    cands = model.get(ctx)
    if not cands:
        return [0.0]*6          # 简化
    words = list(cands.keys())
    total = sum(cands.values())
    probs = []
    for w in ("a", "b", "c", "d", "e", "f"):
        probs.append(cands.get(w, 0)/total)
    return probs

print("  Beam search（B=3）:")
beams = beam_search(lambda step, toks: [0.4, 0.3, 0.1, 0.1, 0.05, 0.05] if step < 3 else [0.2]*6,
                    beam_width=3, steps=3)
for log_p, toks in beams:
    print(f"    P={2**log_p:.4f} tokens={toks}")
print("  Beam Search 保留多条候选路径，适合有唯一正确答案的任务（翻译）")
print("  生成任务（聊天/创作）更适合 top-p 采样：多样性 + 可控质量")

print("\n== 采样策略对比 ==")
print(f"  {'策略':<14}{'多样性':<10}{'质量':<10}{'适用场景'}")
for row in (("greedy", "低", "高(可能重复)", "确定性任务"),
            ("temperature", "可调", "取决于 T", "通用"),
            ("top-k", "中等", "高", "通用"),
            ("top-p", "自适应", "高", "现代 LLM 标准"),
            ("beam search", "低", "最高", "翻译/摘要")):
    print(f"  {row[0]:<14}{row[1]:<10}{row[2]:<10}{row[3]}")

print("\n== 工程要点 ==")
for line in [
    "  temperature/top-k/top-p 是 LLM API 的核心参数（OpenAI/Anthropic）",
    "  多种策略可组合：先 top-p 截断再 temperature 缩放",
    "  repetition penalty 惩罚已生成的 token，防止重复",
    "  与第812课 n-gram、第813课 perplexity、第814课纠错构成完整 NLP 基础",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「repetition penalty」：对已生成的 token 的 logits 除以惩罚系数。
# 2. 实现 min-p 采样：保留概率 > min_p × max_prob 的 token。
# 3. 对比 beam search(B=1,3,5) 与 greedy 的 BLEU 分数差异。
# 4. 思考：为什么聊天任务推荐 top-p=0.9 而翻译任务推荐 beam search？
