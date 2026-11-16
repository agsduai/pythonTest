# ===== 第815课：自然语言处理与语言模型-HMM与维特比算法 =====
# 知识点：
#   - HMM：隐藏状态序列 + 可观测序列；三个概率：初始π、转移A、发射B
#   - 三大问题：评估(前向)、解码(维特比)、学习(Baum-Welch)
#   - Viterbi 算法：动态规划找最优隐状态序列，O(T·|S|²)
#   - 应用：词性标注 POS tagging、语音识别、基因序列分析
#   - 与第678课马尔可夫链：HMM 加了「观测」层，隐藏状态不可直接观测
#   - 本课用小规模词性标注演示完整的 HMM + Viterbi
# 依赖：无（标准库）
import math
from collections import defaultdict, Counter


TRAIN = [
    [("the", "DET"), ("cat", "NOUN"), ("sat", "VERB")],
    [("the", "DET"), ("dog", "NOUN"), ("barked", "VERB")],
    [("a", "DET"), ("cat", "NOUN"), ("ran", "VERB")],
    [("the", "DET"), ("dog", "NOUN"), ("ran", "VERB")],
    [("a", "DET"), ("dog", "NOUN"), ("barked", "VERB")],
    [("the", "DET"), ("cat", "NOUN"), ("sat", "VERB"), ("on", "PREP"), ("a", "DET"), ("mat", "NOUN")],
]


class HMM:
    def __init__(self):
        self.tags = set()
        self.vocab = set()
        self.init_prob = defaultdict(float)
        self.trans_prob = defaultdict(lambda: defaultdict(float))
        self.emit_prob = defaultdict(lambda: defaultdict(float))

    def train(self, tagged_sentences):
        tag_counts = Counter()
        trans_counts = defaultdict(Counter)
        emit_counts = defaultdict(Counter)
        init_counts = Counter()

        for sent in tagged_sentences:
            prev_tag = "<START>"
            for word, tag in sent:
                self.tags.add(tag)
                self.vocab.add(word)
                tag_counts[tag] += 1
                if prev_tag == "<START>":
                    init_counts[tag] += 1
                else:
                    trans_counts[prev_tag][tag] += 1
                emit_counts[tag][word] += 1
                prev_tag = tag

        total_init = sum(init_counts.values())
        for tag, c in init_counts.items():
            self.init_prob[tag] = c / total_init
        for prev, nexts in trans_counts.items():
            total = sum(nexts.values())
            for nxt, c in nexts.items():
                self.trans_prob[prev][nxt] = c / total
        for tag, words in emit_counts.items():
            total = sum(words.values())
            for w, c in words.items():
                self.emit_prob[tag][w] = c / total

    def viterbi(self, sentence):
        """Viterbi 算法：返回最可能的标签序列。"""
        T = len(sentence)
        tags = list(self.tags)
        # dp[i][tag] = (best_log_prob, prev_tag)
        dp = [{} for _ in range(T)]
        back = [{} for _ in range(T)]

        # 初始化
        for tag in tags:
            emit = self.emit_prob[tag].get(sentence[0], 1e-8)
            init = self.init_prob.get(tag, 1e-8)
            dp[0][tag] = math.log(init) + math.log(emit)

        # 递推
        for t in range(1, T):
            for tag in tags:
                emit = self.emit_prob[tag].get(sentence[t], 1e-8)
                best_prev, best_prob = None, -math.inf
                for prev_tag in tags:
                    trans = self.trans_prob[prev_tag].get(tag, 1e-8)
                    score = dp[t-1][prev_tag] + math.log(trans) + math.log(emit)
                    if score > best_prob:
                        best_prob = score; best_prev = prev_tag
                dp[t][tag] = best_prob
                back[t][tag] = best_prev

        # 回溯
        best_last = max(tags, key=lambda t: dp[T-1][t])
        result = [best_last]
        for t in range(T-1, 0, -1):
            result.append(back[t][result[-1]])
        result.reverse()
        return result

    def forward_prob(self, sentence):
        """前向算法：P(观测序列)，用 log sum 避免下溢。"""
        T = len(sentence)
        tags = list(self.tags)
        alpha = [{} for _ in range(T)]
        for tag in tags:
            init = self.init_prob.get(tag, 1e-8)
            emit = self.emit_prob[tag].get(sentence[0], 1e-8)
            alpha[0][tag] = math.log(init) + math.log(emit)
        for t in range(1, T):
            for tag in tags:
                emit = self.emit_prob[tag].get(sentence[t], 1e-8)
                log_sum = -math.inf
                for prev in tags:
                    trans = self.trans_prob[prev].get(tag, 1e-8)
                    log_p = alpha[t-1][prev] + math.log(trans)
                    log_sum = max(log_sum, log_p) + math.log1p(math.exp(min(0, log_sum - max(log_sum, log_p))))
                alpha[t][tag] = log_sum + math.log(emit)
        return max(alpha[T-1].values())  # 简化：取最大而非 log-sum-exp


hmm = HMM()
hmm.train(TRAIN)
print("== 训练后的 HMM 参数 ==")
print("  标签集:", sorted(hmm.tags))
print("  初始概率:", {k: round(v, 3) for k, v in hmm.init_prob.items()})
print("  转移概率 P(NOUN->VERB):", round(hmm.trans_prob["NOUN"].get("VERB", 0), 3))
print("  发射概率 P(VERB|sat):", round(hmm.emit_prob["VERB"].get("sat", 0), 3))

print("\n== Viterbi 解码 ==")
for sent in [("the", "cat", "sat"), ("a", "dog", "barked"),
             ("the", "dog", "ran", "on", "a", "mat"),
             ("the", "fox", "sat"),                      # fox 未见
             ("a", "cat", "barked", "on", "the", "dog")]:
    tags = hmm.viterbi(list(sent))
    pairs = list(zip(sent, tags))
    print(f"  {' '.join(sent):<30} -> {' '.join(tags)}")

print("\n== Viterbi 动态规划表 ==")
sent = ("the", "cat", "sat")
tags = sorted(hmm.tags)
dp = [{} for _ in range(len(sent))]
for tag in tags:
    init = hmm.init_prob.get(tag, 1e-8)
    emit = hmm.emit_prob[tag].get(sent[0], 1e-8)
    dp[0][tag] = math.log(init) + math.log(emit)
for t in range(1, len(sent)):
    for tag in tags:
        emit = hmm.emit_prob[tag].get(sent[t], 1e-8)
        best = max(dp[t-1][pt] + math.log(hmm.trans_prob[pt].get(tag, 1e-8))
                   for pt in tags)
        dp[t][tag] = best

print(f"  句子: {sent}")
for t in range(len(sent)):
    print(f"  t={t} (word={sent[t]!r}):")
    for tag in tags:
        print(f"    {tag:<6} log_prob={dp[t][tag]:>8.3f}")

print("\n== 与朴素贝叶斯的对比 ==")
for line in (
    "  朴素贝叶斯(第36章): 每个词独立分类，不考虑标签间的依赖",
    "  HMM: 考虑标签转移概率（DET->NOUN 比 NOUN->DET 常见）",
    "  HMM 用 Viterbi 找全局最优标签序列，而非逐词独立决策",
):
    print(" ", line)

print("\n== 三大问题 ==")
for line in [
    "  评估 evaluation: 前向算法算 P(观测序列)，O(T·S²)",
    "  解码 decoding: Viterbi 找最优隐状态序列，O(T·S²)",
    "  学习 learning: Baum-Welch(EM) 从无标签数据估计参数",
    "  有标签时用最大似然估计（本课做法），无标签时用 Baum-Welch",
]:
    print("  -", line)

print("\n== 应用 ==")
for line in [
    "  词性标注 POS tagging（本课）、命名实体识别 NER",
    "  语音识别（GMM-HMM → DNN-HMM → 端到端）",
    "  基因序列分析：编码区/非编码区预测",
    "  输入法拼音转汉字（中文 IME 的 Viterbi 解码）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 Baum-Welch 算法的 E 步（前后向概率计算）。
# 2. 给 HMM 加「平滑」（未见过的词给小概率），处理测试集的 OOV。
# 3. 对比 HMM 与「逐词最大概率标签」的准确率差异。
# 4. 思考：为什么 HMM 的 Viterbi 用动态规划而不是穷举所有标签序列？
