# ===== 第431课：机器学习进阶-分类评估指标 =====
# 知识点：
#   - 混淆矩阵：TP/FP/FN/TN，一切指标的源头
#   - 准确率：整体对的比例；类别不平衡时会“骗人”
#   - 精确率 P=TP/(TP+FP)：说正的有多少真对；召回率 R=TP/(TP+FN)：真的抓回多少
#   - F1 = 2PR/(P+R)：精确率与召回率的调和平均
#   - ROC 曲线：横轴 FPR、纵轴 TPR，遍历阈值得到；AUC 越接近 1 越好
#   - 阈值选择是业务问题：宁可错杀（高召回）还是宁可漏判（高精确）
# 依赖：pip install numpy

import numpy as np


def confusion_matrix(y_true, y_pred):
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    return tp, fp, fn, tn


def metrics(y_true, y_pred):
    tp, fp, fn, tn = confusion_matrix(y_true, y_pred)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / len(y_true)
    specificity = tn / (tn + fp) if tn + fp else 0.0
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn,
            "准确率": accuracy, "精确率": precision,
            "召回率": recall, "F1": f1, "特异度": specificity}


def roc_auc(y_true, scores):
    """按分数从高到低扫阈值，计算 ROC 点与 AUC（梯形法）。"""
    order = np.argsort(-scores)
    y_sorted = y_true[order]
    positives = y_sorted.sum()
    negatives = len(y_sorted) - positives
    tprs, fprs = [0.0], [0.0]
    tp = fp = 0
    for label in y_sorted:
        if label == 1:
            tp += 1
        else:
            fp += 1
        tprs.append(tp / positives)
        fprs.append(fp / negatives)
    auc = 0.0
    for i in range(1, len(fprs)):
        auc += (fprs[i] - fprs[i - 1]) * (tprs[i] + tprs[i - 1]) / 2
    return np.array(fprs), np.array(tprs), float(auc)


# ---- 数据：两类分数的分布（正类偏高，但重叠）----
rng = np.random.default_rng(9)
n = 400
y_true = (rng.random(n) < 0.3).astype(int)
scores = np.where(
    y_true == 1,
    rng.normal(0.68, 0.18, n),
    rng.normal(0.32, 0.18, n),
).clip(0, 1)

# ---- 阈值 0.5 的指标 ----
y_pred = (scores >= 0.5).astype(int)
print("== 阈值 0.5 ==")
for k, v in metrics(y_true, y_pred).items():
    print(f"  {k:6s} {v:.3f}" if isinstance(v, float) else f"  {k:6s} {v}")

# ---- 阈值扫描：观察精确率/召回率互换 ----
print("\n== 阈值扫描 ==")
print(f"  {'阈值':>4s} {'精确率':>7s} {'召回率':>7s} {'F1':>7s}")
best_th, best_f1 = 0.5, -1
for th in np.arange(0.2, 0.81, 0.1):
    m = metrics(y_true, (scores >= th).astype(int))
    print(f"  {th:4.1f} {m['精确率']:7.3f} {m['召回率']:7.3f} {m['F1']:7.3f}")
    if m["F1"] > best_f1:
        best_th, best_f1 = round(float(th), 1), m["F1"]
print(f"  按 F1 选出的阈值：{best_th}（F1={best_f1:.3f}）")

# ---- ROC / AUC ----
fprs, tprs, auc = roc_auc(y_true, scores)
print(f"\n== ROC / AUC ==\n  AUC = {auc:.3f}（0.5 等于瞎猜，1.0 完美）")
print("  ROC 关键点（FPR, TPR）：")
for i in (0, len(fprs) // 4, len(fprs) // 2, 3 * len(fprs) // 4, -1):
    print(f"    ({fprs[i]:.3f}, {tprs[i]:.3f})")

# ---- 类别不平衡的“准确率陷阱” ----
print("\n== 准确率陷阱 ==")
imbalanced_true = np.zeros(1000, dtype=int)
imbalanced_true[:30] = 1                       # 只有 3% 正类
always_negative = np.zeros(1000, dtype=int)
print("  全预测为负的准确率：", f"{(always_negative == imbalanced_true).mean():.3f}")
print("  但召回率：", f"{metrics(imbalanced_true, always_negative)['召回率']:.3f}")
print("  结论：不平衡数据要看精确率/召回率/F1/AUC，不能只看准确率")

# ===== 练习题 =====
# 1. 写一个函数按“目标召回率 >= 0.8”选阈值。
# 2. 用 PR 曲线（精确率-召回率）替代 ROC，比较两者适用场景。
# 3. 给 metrics 增加“约登指数”（TPR - FPR）并找最优阈值。
# 4. 思考：医疗筛查与垃圾邮件过滤，分别该优先精确率还是召回率？
