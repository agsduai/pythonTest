# ===== 第386课：文本处理与搜索-朴素贝叶斯文本分类 =====
# 知识点：
#   - 朴素贝叶斯：用贝叶斯公式 + “特征独立”假设做分类
#   - P(类别|文本) ∝ P(类别) × Π P(词|类别)
#   - 拉普拉斯平滑：给每个词加 1，避免“训练集没出现 → 概率 0”
#   - 用对数概率连加：防止大量小数相乘下溢为 0
#   - 文本分类的经典基线：垃圾邮件、情感分析、主题归类
# 依赖：无（标准库 math / collections）

import math
from collections import Counter, defaultdict

# ---- 训练语料：6 条短信，spam=垃圾短信，ham=正常 ----
TRAIN = [
    ("win free money now click here", "spam"),
    ("cheap loan limited offer apply now", "spam"),
    ("free gift for you hurry up", "spam"),
    ("meeting at 3pm tomorrow", "ham"),
    ("project report attached please review", "ham"),
    ("lunch with team today", "ham"),
]


def tokenize(text: str) -> list[str]:
    return text.lower().split()


class NaiveBayes:

    def __init__(self):
        self.prior = {}
        self.word_counts = defaultdict(Counter)
        self.class_counts = Counter()
        self.vocab = set()

    def train(self, samples):
        for text, label in samples:
            self.class_counts[label] += 1
            for word in tokenize(text):
                self.word_counts[label][word] += 1
                self.vocab.add(word)
        total = sum(self.class_counts.values())
        self.prior = {c: n / total for c, n in self.class_counts.items()}

    def predict_proba(self, text: str) -> dict[str, float]:
        """返回两类别的对数后验（做归一化后即概率）。"""
        tokens = tokenize(text)
        V = len(self.vocab)
        scores = {}
        for label in self.class_counts:
            # log P(类别)
            score = math.log(self.prior[label])
            total_words = sum(self.word_counts[label].values())
            # 每个词 log P(词|类别)，加 1 平滑
            for word in tokens:
                score += math.log(
                    (self.word_counts[label][word] + 1) / (total_words + V)
                )
            scores[label] = score
        return scores

    def predict(self, text: str) -> str:
        scores = self.predict_proba(text)
        best = max(scores, key=scores.get)
        print(f"  {text!r} → {scores} → 判为 {best}")
        return best


nb = NaiveBayes()
nb.train(TRAIN)

print("类别先验：", nb.prior)
print("词表大小：", len(nb.vocab))
print("\n预测结果：")
cases = [
    "free money click now",          # 明显 spam
    "meeting report review",          # 明显 ham
    "free lunch with team today",     # 两边都有词，看谁更强
    "limited offer for project",      # 混合
]
for text in cases:
    nb.predict(text)

# ---- 用“留一法”粗估准确率（样本少，仅演示思路）----
print("\n留一法评估：")
correct = 0
for i, (text, label) in enumerate(TRAIN):
    others = TRAIN[:i] + TRAIN[i + 1:]
    model = NaiveBayes()
    model.train(others)
    pred = max(model.predict_proba(text), key=model.predict_proba(text).get)
    correct += (pred == label)
print(f"  准确率 {correct}/{len(TRAIN)} = {correct / len(TRAIN):.2f}")
print("  （样本极少时留一法波动大，真实项目需要更多数据）")

# ===== 练习题 =====
# 1. 增加 3 条 spam 样本，重新跑预测，观察“free lunch”这条是否翻盘。
# 2. 去掉拉普拉斯平滑（+1 改成 +0），观察未登录词导致的问题。
# 3. 用“不加 log”的概率连乘实现一次，输入长文本观察下溢为 0。
# 4. 思考：朴素贝叶斯的“朴素”指什么假设？它为什么不影响效果太好？
