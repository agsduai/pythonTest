# ===== 第433课：机器学习进阶-模型持久化与版本管理 =====
# 知识点：
#   - 训练一次、推理多次：模型必须能落盘（pickle），否则每次启动都要重训
#   - 只存权重不够：特征顺序、预处理参数、版本号、训练指标都要一起存
#   - 元数据用 JSON（人可读），权重用 pickle（保留类型）
#   - 加载时校验版本与特征数：不匹配就拒绝，而不是“带病预测”
#   - 安全：pickle 只加载自己产出的文件（第400课）
# 依赖：pip install numpy

import json
import pickle
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np

MODEL_VERSION = "1.0"


# ---------------- 训练一个简单逻辑回归（复用第378课）----------------
def sigmoid(z):
    out = np.empty_like(z, dtype=float)
    pos = z >= 0
    out[pos] = 1 / (1 + np.exp(-z[pos]))
    exp_z = np.exp(z[~pos])
    out[~pos] = exp_z / (1 + exp_z)
    return out


def train_logistic(X, y, lr=0.5, epochs=2000):
    w = np.zeros(X.shape[1])
    for _ in range(epochs):
        p = sigmoid(X @ w)
        w -= lr * (1 / len(y)) * X.T @ (p - y)
    return w


rng = np.random.default_rng(4)
n = 300
X_raw = np.vstack([
    rng.normal([2, 2], [1, 1.2], size=(n // 2, 2)),
    rng.normal([4.5, 4.5], [1, 1.2], size=(n // 2, 2)),
])
y = np.r_[np.zeros(n // 2), np.ones(n // 2)]

mean, std = X_raw.mean(axis=0), X_raw.std(axis=0)
X = np.c_[np.ones(n), (X_raw - mean) / std]     # 标准化 + 偏置
w = train_logistic(X, y)
acc = float(np.mean((sigmoid(X @ w) >= 0.5) == y))
print("训练完成，权重：", w.round(3), "| 训练准确率：", round(acc, 3))

FEATURES = ["feature_a", "feature_b"]


# ---------------- 保存：权重 + 元数据 ----------------
def save_model(path: Path, weights, mean_, std_, features, metrics):
    bundle = {
        "version": MODEL_VERSION,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "features": features,
        "weights": weights,
        "mean": mean_,
        "std": std_,
        "metrics": metrics,
    }
    with open(path, "wb") as f:
        pickle.dump(bundle, f, protocol=pickle.HIGHEST_PROTOCOL)
    return path


def load_model(path: Path, expected_features=None):
    """加载并校验：版本、特征列表、权重长度。"""
    with open(path, "rb") as f:
        bundle = pickle.load(f)
    if bundle.get("version") != MODEL_VERSION:
        raise ValueError(f"模型版本不兼容：{bundle.get('version')} != {MODEL_VERSION}")
    if expected_features and bundle["features"] != expected_features:
        raise ValueError(f"特征不匹配：{bundle['features']} != {expected_features}")
    if len(bundle["weights"]) != len(bundle["features"]) + 1:
        raise ValueError("权重长度与特征数不一致，模型文件可能损坏")
    return bundle


def predict(bundle, X_new):
    X_new = np.atleast_2d(X_new)
    if X_new.shape[1] != len(bundle["features"]):
        raise ValueError(f"输入特征数应为 {len(bundle['features'])}")
    z = (X_new - bundle["mean"]) / bundle["std"]
    z = np.c_[np.ones(len(z)), z]
    return sigmoid(z @ bundle["weights"])


with tempfile.TemporaryDirectory() as tmp:
    model_path = Path(tmp) / "model.pkl"
    meta_path = Path(tmp) / "model_meta.json"

    save_model(model_path, w, mean, std, FEATURES,
               {"accuracy": round(acc, 4), "samples": n})
    print(f"\n模型已保存：{model_path.name}（{model_path.stat().st_size} 字节）")

    # 元数据另存为 JSON，便于监控/对比（不含二进制）
    meta_path.write_text(json.dumps({
        "version": MODEL_VERSION, "features": FEATURES,
        "accuracy": round(acc, 4), "samples": n,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("元数据：", json.loads(meta_path.read_text(encoding="utf-8")))

    # ---- 加载并预测 ----
    loaded = load_model(model_path, FEATURES)
    for point in ([1.5, 1.5], [5.0, 5.0]):
        prob = predict(loaded, point)[0]
        print(f"  新样本 {point} → 类别 1 概率 {prob:.3f}，预测 {int(prob >= 0.5)}")

    # ---- 校验失败示例 ----
    print("\n== 加载校验 ==")
    try:
        load_model(model_path, ["a", "b", "c"])       # 特征数不符
    except ValueError as exc:
        print("  拦截：", exc)

    bad = dict(loaded, version="0.9")
    bad_path = Path(tmp) / "old.pkl"
    with open(bad_path, "wb") as f:
        pickle.dump(bad, f)
    try:
        load_model(bad_path, FEATURES)
    except ValueError as exc:
        print("  拦截：", exc)

    # ---- 损坏的特征顺序：必须报错而不是悄悄算错 ----
    try:
        predict(loaded, [[1, 2, 3]])
    except ValueError as exc:
        print("  拦截：", exc)

# 生产建议：
#   模型文件带版本号 + 训练数据摘要；上线前做 A/B 或影子流量
#   保留最近 N 个模型，回滚有路（第278课备份思路）

# ===== 练习题 =====
# 1. 增加“特征顺序 hash”，加载时校验顺序完全一致。
# 2. 把保存格式改成 joblib/ONNX（了解即可），比较体积与速度。
# 3. 写一个 ModelRegistry 类：按版本号保存/加载/列出模型。
# 4. 思考：为什么“只保存权重”在换了预处理参数后会悄悄算错？
