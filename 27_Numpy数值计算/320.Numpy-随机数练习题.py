# ===== 第320课：Numpy-随机数 =====
# 知识点：
#   - 传统接口：np.random.seed 设种子 → randint / rand / normal / choice / shuffle
#   - 种子：固定种子 = 结果可复现（调试、出题、测试的刚需）
#   - 现代接口（推荐）：rng = np.random.default_rng(种子)
#   - 与第234课对照：科学模拟用 numpy，安全令牌仍必须 secrets
# 依赖：pip install numpy

import numpy as np

# ---- 传统接口：先固定种子 ----
np.random.seed(42)
print("掷 5 次骰子：", np.random.randint(1, 7, size=5))
print("均匀分布：", np.random.rand(2, 3).round(2))
print("正态分布（身高 均值170 标准差8）：", np.random.normal(170, 8, 5).round(1))
print("抽签：", np.random.choice(["石头", "剪刀", "布"], size=3))

deck = np.arange(1, 11)
np.random.shuffle(deck)              # 原地洗牌
print("洗牌：", deck)
print("不重复抽 3 张：", np.random.choice(deck, size=3, replace=False))

# 种子让“随机”可复现
np.random.seed(42)
again = np.random.randint(1, 7, size=5)
np.random.seed(42)
same = np.random.randint(1, 7, size=5)
print("同种子结果相同：", list(again) == list(same))

# ---- 现代接口：Generator ----
rng = np.random.default_rng(42)
print("default_rng 掷骰子：", rng.integers(1, 7, size=5))
print("正态：", rng.normal(100, 15, 5).round(1))

# ===== 练习题 =====
# 1. 模拟掷两个骰子 10000 次，用第319课技巧统计点数和的分布。
# 2. 用 default_rng 生成 10 个“班级身高”（均值 165，标准差 10，取整）。
# 3. 思考：为什么模拟实验要写死种子，而抽奖程序绝不能写死？
