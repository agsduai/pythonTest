# ===== 第814课：自然语言处理与语言模型-拼写纠错与噪声信道 =====
# 知识点：
#   - 噪声信道模型：原始词 w 经噪声变成错误词 s，找 P(w)·P(s|w) 最大的 w
#   - 编辑距离（第36章）给出「一个错误」的候选：替换/插入/删除/换位
#   - 拼写纠错 = 在候选集中选「先验频率 × 噪声概率」最高的词
#   - 简化版：编辑距离 1 的候选 + 语料频率排序（Norvig 2007 方案）
#   - 编辑距离 2：对每个距离 1 候选再做一轮距离 1 的变换
#   - 与第36章编辑距离的区别：36 只算距离，这里用距离生成候选并做概率选择
# 依赖：无（标准库）
import math
import re
from collections import Counter

LETTERS = "abcdefghijklmnopqrstuvwxyz"


def edits1(word):
    """生成与 word 编辑距离为 1 的所有可能串。"""
    splits = [(word[:i], word[i:]) for i in range(len(word)+1)]
    deletes = [a+b[1:] for a, b in splits if b]
    transposes = [a+b[1]+b[0]+b[2:] for a, b in splits if len(b) > 1]
    replaces = [a+c+b[1:] for a, b in splits if b for c in LETTERS]
    inserts = [a+c+b for a, b in splits for c in LETTERS]
    return set(deletes + transposes + replaces + inserts)


def edits2(word):
    return set(e2 for e1 in edits1(word) for e2 in edits1(e1))


CORPUS = """
the quick brown fox jumps over the lazy dog the quick brown fox
the cat sat on the mat the quick brown fox jumps over the lazy dog
hello world hello world hello there the quick brown fox
the world is a stage the world is round the quick brown fox
the cat and the hat the cat in the hat the cat sat on the mat
the fox ran the fox ran away the fox and the dog hello world
"""

WORDS = Counter(re.findall(r"[a-z]+", CORPUS.lower()))
TOTAL = sum(WORDS.values())


def probability(word):
    return WORDS[word] / TOTAL if word in WORDS else 0.0


def correct(word):
    """Norvig 拼写纠错：优先级 已知词 > edit1 已知 > edit2 已知 > 原词。"""
    candidates = (known([word]) or
                  known(edits1(word)) or
                  known(edits2(word)) or
                  [word])
    return max(candidates, key=probability)


def known(words):
    return set(w for w in words if w in WORDS)


print("== 训练词表 ==")
print(f"  词汇量={len(WORDS)}, 总词数={TOTAL}")
print(f"  前 10 高频: {WORDS.most_common(10)}")

print("\n== 编辑距离 1 的候选数 ==")
for word in ("the", "wrold", "quik", "cat"):
    e1 = edits1(word)
    e1_known = known(e1)
    print(f"  {word!r}: edit1 候选={len(e1)} 其中已知={len(e1_known)} "
          f"已知子集={sorted(e1_known)[:5]}")

print("\n== 拼写纠错 ==")
typos = ["teh", "wrold", "quik", "cat", "brwon", "jumps", "lazzy", "houes"]
for typo in typos:
    if typo in WORDS:
        print(f"  {typo!r:<10} -> 本身是已知词，返回原文")
    else:
        c = correct(typo)
        print(f"  {typo!r:<10} -> {c!r}  P={probability(c):.4f}")

print("\n== 噪声信道模型：P(w)·P(s|w) ==")
def noisy_channel_score(s, w):
    """假设只有一个替换错误，P(s|w) ≈ 1/(字表大小)（均匀），主要靠 P(w) 排序。"""
    if s == w: return math.inf
    return math.log(probability(w)) if w in WORDS else -math.inf

for typo in ("teh", "wrold"):
    cands = known(edits1(typo))
    ranked = sorted(cands, key=lambda w: -noisy_channel_score(typo, w))[:3]
    print(f"  {typo!r} 的候选（按 P(w) 排序）: {ranked}")
    print(f"    最优: {correct(typo)!r}")

print("\n== 编辑距离 2 的纠错能力 ==")
for word in ("tehh", "wrld", "quikc"):
    e1 = known(edits1(word))
    e2 = known(edits2(word))
    c = correct(word)
    print(f"  {word!r}: edit1 已知={sorted(e1)} edit2 已知数={len(e2)} -> {c!r}")
print("  edit2 候选爆炸：len(word)² × 26²，但 set 去重后可控")

print("\n== 性能分析 ==")
import time
for word in ("calclate", "informatoin"):
    t0 = time.perf_counter()
    c = correct(word)
    dt = (time.perf_counter()-t0)*1000
    print(f"  correct({word!r}) = {c!r} 耗时={dt:.1f}ms")
print("  edits2 的 set 运算 dominates；生产用 BK-tree 或 SymSpell 加速")

print("\n== 工程方案 ==")
for line in [
    "  Norvig 方案：本课，最简单，对单字符 typo 效果好",
    "  SymSpell：预计算 edit distance ≤ 2 的删除变体，查表 O(1)",
    "  BK-tree：用编辑距离度量建树，剪枝查询",
    "  深度学习方案：seq2seq / BERT 掩码预测（处理语法级错误）",
]:
    print("  -", line)

print("\n== 语言模型增强 ==")
for line in (
    "  纯编辑距离只看词形，不知道上下文",
    "  加上下文：P(candidate | 前后文) 用 n-gram 或 LLM 评分（第812课）",
    "  例：「I can't sea」→ sea 是正确拼写但上下文应为 see",
    "  完整方案：候选生成(编辑距离) × 上下文排序(n-gram) 两阶段",
):
    print(" ", line)

# ===== 练习题 =====
# 1. 用 n-gram 语言模型（第812课）给编辑纠错候选加上下文评分。
# 2. 实现支持「换位+替换+插入+删除」各带不同错误概率的噪声信道。
# 3. 用 Spellchecker 评估集（如 Birkbeck）测试准确率。
# 4. 思考：为什么「编辑距离 2」能覆盖绝大多数真实拼写错误？
