# ===== 第381课：机器学习入门-综合案例-房价预测 =====
# 知识点：
#   - 全流程串讲：造数据 → 划分 → 标准化 → 训练 → 评估 → 解释 → 落盘
#   - 多特征线性回归：面积、房龄、距离地铁 → 房价
#   - 指标三件套：MAE（平均绝对误差）、RMSE（均方根误差）、R²
#   - 标准化后的系数 = 特征重要性（量纲统一后才能比较）
#   - 残差分析：看模型在哪些样本上“系统性偏错”
# 依赖：pip install numpy

import csv
import os

import numpy as np


def train_test_split(X, y, test_size=0.2, seed=2026):
    idx = np.random.default_rng(seed).permutation(len(X))
    n_test = int(len(X) * test_size)
    return X[idx[n_test:]], X[idx[:n_test]], y[idx[n_test:]], y[idx[:n_test]]


def standardize(train, test):
    mean, std = train.mean(axis=0), train.std(axis=0)
    std[std == 0] = 1
    return (train - mean) / std, (test - mean) / std, mean, std


def fit_lstsq(X, y):
    Xb = np.c_[np.ones(len(X)), X]
    w, *_ = np.linalg.lstsq(Xb, y, rcond=None)
    return w


def predict(X, w):
    return np.c_[np.ones(len(X)), X] @ w


def metrics(y_true, y_pred):
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    r2 = 1 - np.sum((y_true - y_pred) ** 2) / np.sum((y_true - y_true.mean()) ** 2)
    return {"MAE": mae, "RMSE": rmse, "R2": float(r2)}


# ---- 1. 造数据：面积(㎡)、房龄(年)、距地铁(km) → 房价(万) ----
rng = np.random.default_rng(2026)
n = 500
area = rng.uniform(50, 160, n)
age = rng.uniform(0, 30, n)
distance = rng.uniform(0.2, 8, n)

# 真实规律：面积每平 3 万；房龄每年折 0.8 万；离地铁每 km 折 12 万；基础价 60 万
price = 3 * area - 0.8 * age - 12 * distance + 60 + rng.normal(0, 8, n)
X_raw = np.c_[area, age, distance]

# ---- 2. 划分 + 标准化（只用训练集统计量）----
X_train, X_test, y_train, y_test = train_test_split(X_raw, price)
X_train_s, X_test_s, mean, std = standardize(X_train, X_test)
print(f"训练 {len(X_train)} / 测试 {len(X_test)}")
print("训练集特征均值：", mean.round(2), "| 标准差：", std.round(2))

# ---- 3. 训练 + 评估 ----
w = fit_lstsq(X_train_s, y_train)
train_pred = predict(X_train_s, w)
test_pred = predict(X_test_s, w)

print("\n训练集指标：", {k: round(v, 2) for k, v in metrics(y_train, train_pred).items()})
print("测试集指标：", {k: round(v, 2) for k, v in metrics(y_test, test_pred).items()})

# ---- 4. 特征重要性（标准化系数，去掉偏置）----
names = ["面积", "房龄", "距地铁"]
print("\n特征系数（标准化后，绝对值=影响力）：")
for name, coef in zip(names, w[1:]):
    direction = "正向" if coef > 0 else "负向"
    print(f"  {name}: {coef:+.2f}（{direction}）")
print(f"  截距（基准价）: {w[0]:.2f} 万")

# ---- 5. 残差分析：找出模型最“看不懂”的 3 个样本 ----
residuals = y_test - test_pred
worst = np.argsort(np.abs(residuals))[-3:][::-1]
print("\n残差最大的 3 个测试样本：")
for i in worst:
    print(f"  面积 {X_test[i, 0]:.1f}㎡ 房龄 {X_test[i, 1]:.1f}年 "
          f"距离 {X_test[i, 2]:.1f}km | 真实 {y_test[i]:.1f} 预测 {test_pred[i]:.1f} "
          f"| 残差 {residuals[i]:+.1f}")

# ---- 6. 预测一套新房 ----
new_house = np.array([[100, 5, 1.0]])
new_s = (new_house - mean) / std
print(f"\n新房 {new_house[0]}（面积㎡/房龄年/距离km）预测房价：{predict(new_s, w)[0]:.2f} 万")

# ---- 7. 落盘预测结果（CSV，utf-8-sig）----
with open("predictions_381.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["面积", "房龄", "距地铁", "真实房价", "预测房价", "残差"])
    for i in range(len(X_test)):
        writer.writerow([*X_test[i].round(2), round(float(y_test[i]), 2),
                         round(float(test_pred[i]), 2), round(float(residuals[i]), 2)])
print("预测明细已写入 predictions_381.csv")

os.remove("predictions_381.csv")

# ===== 练习题 =====
# 1. 增加第四个特征“是否学区房”（0/1），重新训练并看 R²。
# 2. 故意用“全体数据”标准化（数据泄漏），对比测试集指标是否虚高。
# 3. 把噪声标准差改成 25，观察 MAE 与 R² 的变化，说明“模型不是万能的”。
# 4. 思考：如果真实关系是非线性的（面积平方影响价格），线性回归会怎样？
