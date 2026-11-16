# ===== 第375课：机器学习入门-特征缩放与数据划分 =====
# 知识点：
#   - 训练/测试划分：随机打乱后按比例切分，测试集模拟“未来的新数据”
#   - 数据泄漏：任何预处理（均值/方差）只能用训练集统计量
#   - 标准化 z-score：(x - 训练均值) / 训练标准差 —— 线性模型/KNN 的标配
#   - 归一化 MinMax：映射到 [0,1]，对异常值敏感
#   - 为什么必须缩放：量纲差异会让“距离”被大数值特征主导
# 依赖：pip install numpy

import numpy as np


def train_test_split(X, y, test_size=0.2, seed=42):
    """按比例随机划分，返回 X_train, X_test, y_train, y_test。"""
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(X))              # 打乱下标
    n_test = int(len(X) * test_size)
    test_idx, train_idx = idx[:n_test], idx[n_test:]
    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]


class StandardScaler:
    """只用训练集 fit，再 transform 训练集和测试集。"""

    def fit(self, X):
        self.mean_ = X.mean(axis=0)
        self.std_ = X.std(axis=0)
        self.std_[self.std_ == 0] = 1.0        # 防止常量列除零
        return self

    def transform(self, X):
        return (X - self.mean_) / self.std_

    def fit_transform(self, X):
        return self.fit(X).transform(X)


class MinMaxScaler:

    def fit(self, X):
        self.min_ = X.min(axis=0)
        self.max_ = X.max(axis=0)
        self.range_ = np.where(self.max_ - self.min_ == 0, 1, self.max_ - self.min_)
        return self

    def transform(self, X):
        return (X - self.min_) / self.range_

    def fit_transform(self, X):
        return self.fit(X).transform(X)


# ---- 演示数据：身高(cm) 与 年龄(岁)，量纲差 5 倍以上 ----
rng = np.random.default_rng(0)
n = 200
X = np.c_[rng.normal(170, 8, n), rng.normal(30, 5, n)]
y = (0.4 * X[:, 0] + 1.5 * X[:, 1] + rng.normal(0, 3, n))
print("原始数据前 3 行：\n", X[:3].round(1))

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25)
print(f"\n划分结果：训练 {len(X_train)} 条，测试 {len(X_test)} 条")
print("训练集均值：", X_train.mean(axis=0).round(1), "（测试集不参与统计）")

# ---- 缩放前后对比 ----
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)      # 用训练集统计量
X_test_s = scaler.transform(X_test)            # 测试集只 transform

print("\n缩放后训练均值：", X_train_s.mean(axis=0).round(2))
print("缩放后训练标准差：", X_train_s.std(axis=0).round(2))
print("测试集均值（不要求为 0，但应在 0 附近）：", X_test_s.mean(axis=0).round(2))

# ---- 距离视角：缩放如何改变“谁离谁近” ----
sample = X_train[0]
dist_raw = np.linalg.norm(X_train - sample, axis=1)[:5].round(1)
sample_s = X_train_s[0]
dist_scaled = np.linalg.norm(X_train_s - sample_s, axis=1)[:5].round(2)
print("\n原始量纲下前 5 个距离：", dist_raw)
print("标准化后前 5 个距离：", dist_scaled)
print("说明：原始距离几乎由身高（数值大）主导，年龄的贡献被淹没")

# ===== 练习题 =====
# 1. 把测试集比例改成 0.5，观察训练样本量对后续模型的影响。
# 2. 用 MinMaxScaler 处理同一份数据，打印缩放后的最大最小值。
# 3. 故意用“全体数据”算均值方差再缩放（数据泄漏），对比与正确写法的差异。
# 4. 思考：树模型（第254课）为什么通常不需要特征缩放？
