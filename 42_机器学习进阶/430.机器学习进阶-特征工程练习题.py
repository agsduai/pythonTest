# ===== 第430课：机器学习进阶-特征工程 =====
# 知识点：
#   - 特征工程：把原始字段变成“模型好学”的特征，常比换模型收益更大
#   - 常用手法：独热编码、分箱、交互特征、比率特征、时间特征、标准化
#   - 类别特征不能直接当数字：A/B/C 编码成 1/2/3 会让模型误以为有大小
#   - 特征不是越多越好：无关特征引入噪声，需配合评估（第429课）
#   - 本课用 pandas 做变换，用 NumPy 线性回归对比“原始特征 vs 工程特征”
# 依赖：pip install pandas numpy

import numpy as np
import pandas as pd


def make_data(n=300, seed=7):
    rng = np.random.default_rng(seed)
    city = rng.choice(["北京", "上海", "深圳"], size=n)
    age = rng.integers(20, 61, n)
    income = rng.normal(20000, 6000, n).clip(5000, 50000)
    years = rng.integers(0, 11, n)
    city_bonus = {"北京": 1500, "上海": 1200, "深圳": 800}
    spending = (2000 + 0.12 * income + 300 * years
                + np.array([city_bonus[c] for c in city])
                + rng.normal(0, 1500, n))
    return pd.DataFrame({"city": city, "age": age, "income": income,
                         "years": years, "spending": spending})


df = make_data()
print("== 原始数据 ==")
print(df.head(3).to_string(index=False))

# ---------------- 特征工程 ----------------
def engineer(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    # 1) 独热编码：类别 → 0/1 列（drop_first 避免完全共线）
    out = pd.get_dummies(out, columns=["city"], drop_first=True, dtype=int)
    # 2) 分箱：年龄 → 年龄段（有序类别）
    out["age_group"] = pd.cut(out["age"], bins=[19, 30, 40, 50, 61],
                              labels=["20s", "30s", "40s", "50+"])
    out = pd.get_dummies(out, columns=["age_group"], drop_first=True, dtype=int)
    # 3) 交互特征：收入 × 年限（长期高收入客户）
    out["income_x_years"] = out["income"] * out["years"]
    # 4) 比率特征：收入 / 年龄（相对购买力）
    out["income_per_age"] = out["income"] / out["age"]
    # 5) 对数变换：收入右偏 → log 后更接近正态
    out["log_income"] = np.log1p(out["income"])
    return out


engineered = engineer(df)
print("\n== 工程后新增列 ==")
print([c for c in engineered.columns if c not in df.columns])
print(engineered.head(3).to_string(index=False))


# ---------------- 线性回归（第376课）----------------
def add_bias(X):
    return np.c_[np.ones(len(X)), X]


def fit_lstsq(X, y):
    w, *_ = np.linalg.lstsq(X, y, rcond=None)
    return w


def r2(y_true, y_pred):
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - y_true.mean()) ** 2)
    return 1 - ss_res / ss_tot


def evaluate(features: pd.DataFrame, target: pd.Series, seed=1):
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(features))
    split = int(len(features) * 0.75)
    train, test = idx[:split], idx[split:]

    X = features.to_numpy(dtype=float)
    y = target.to_numpy(dtype=float)
    # 只用训练集统计量标准化
    mean, std = X[train].mean(axis=0), X[train].std(axis=0)
    std[std == 0] = 1
    X_train = add_bias((X[train] - mean) / std)
    X_test = add_bias((X[test] - mean) / std)

    w = fit_lstsq(X_train, y[train])
    train_r2 = r2(y[train], X_train @ w)
    test_r2 = r2(y[test], X_test @ w)
    return train_r2, test_r2


# 原始特征（城市要先编码，否则不能进模型）
raw = pd.get_dummies(df.drop(columns=["spending"]), columns=["city"], dtype=int)
train_r2_raw, test_r2_raw = evaluate(raw, df["spending"])
print("\n== 模型对比 ==")
print(f"  原始特征：训练 R² {train_r2_raw:.4f} | 测试 R² {test_r2_raw:.4f}")

eng_features = engineered.drop(columns=["spending"])
train_r2_eng, test_r2_eng = evaluate(eng_features, df["spending"])
print(f"  工程特征：训练 R² {train_r2_eng:.4f} | 测试 R² {test_r2_eng:.4f}")
print(f"  测试集提升：{(test_r2_eng - test_r2_raw) * 100:+.2f} 个百分点")

# ---- 特征数量与过拟合的提醒 ----
print("\n== 特征重要性（标准化系数绝对值前 5）==")
X = eng_features.to_numpy(dtype=float)
y = df["spending"].to_numpy(dtype=float)
mean, std = X.mean(axis=0), X.std(axis=0)
std[std == 0] = 1
w = fit_lstsq(add_bias((X - mean) / std), y)
coefs = sorted(zip(eng_features.columns, w[1:]), key=lambda kv: -abs(kv[1]))[:5]
for name, coef in coefs:
    print(f"  {name:20s} {coef:+.2f}")

# 经验：
#   - 先理解业务，再设计特征（“收入/年龄”比“收入 + 年龄”更有解释力）
#   - 每加一批特征都要重新评估，宁可少而精
#   - 类别特征乱编码是新手最常见的坑

# ===== 练习题 =====
# 1. 增加“城市 × 年限”交互列，观察测试 R² 是否提升。
# 2. 把 income 分箱（低/中/高）替代 log 变换，对比效果。
# 3. 故意加入 20 列随机噪声特征，观察测试 R² 下降。
# 4. 思考：特征工程与“数据泄漏”最容易在哪里撞车？
