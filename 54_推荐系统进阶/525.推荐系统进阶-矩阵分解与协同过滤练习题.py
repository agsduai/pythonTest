# ===== 第525课：推荐系统进阶-矩阵分解与协同过滤 =====
# 知识点：
#   - 协同过滤：用“用户-物品评分矩阵”的相似性做推荐（第432课）
#   - 矩阵分解：把 m×n 的稀疏矩阵拆成 用户向量 × 物品向量（潜在因子）
#   - 预测：r_ui ≈ 全局均值 + 用户偏置 + 物品偏置 + P_u · Q_i
#   - 训练：对已有评分做 SGD，最小化平方误差 + 正则
#   - 优点：能捕捉“潜在口味”，比用户相似度更泛化
#   - 冷启动：新用户/新物品没有评分，向量学不出来（第528课）
# 依赖：pip install numpy

import numpy as np

# 用户-物品评分矩阵（0 表示未评分）
RATINGS = np.array([
    [5, 4, 0, 0, 1, 0],   # 小明
    [4, 5, 0, 0, 2, 0],   # 小红
    [0, 0, 5, 4, 0, 1],   # 小刚
    [0, 0, 4, 5, 0, 2],   # 小丽
    [5, 5, 0, 1, 0, 0],   # 小强
], dtype=float)
USER_NAMES = ["小明", "小红", "小刚", "小丽", "小强"]
ITEM_NAMES = ["Python", "算法", "前端", "设计", "数据库", "后端"]


def train_mf(ratings, k=4, epochs=3000, lr=0.01, reg=0.02, seed=42):
    rng = np.random.default_rng(seed)
    m, n = ratings.shape
    mask = ratings > 0

    mu = ratings[mask].mean()
    bu = np.zeros(m)
    bi = np.zeros(n)
    P = rng.normal(0, 0.1, (m, k))
    Q = rng.normal(0, 0.1, (n, k))

    for epoch in range(1, epochs + 1):
        for u in range(m):
            for i in range(n):
                if ratings[u, i] == 0:
                    continue
                pred = mu + bu[u] + bi[i] + P[u] @ Q[i]
                err = ratings[u, i] - pred
                bu[u] += lr * (err - reg * bu[u])
                bi[i] += lr * (err - reg * bi[i])
                P_u, Q_i = P[u].copy(), Q[i].copy()
                P[u] += lr * (err * Q_i - reg * P_u)
                Q[i] += lr * (err * P_u - reg * Q_i)

        if epoch % 1000 == 0:
            pred = mu + bu[:, None] + bi[None, :] + P @ Q.T
            rmse = np.sqrt(np.mean((pred[mask] - ratings[mask]) ** 2))
            print(f"  epoch {epoch:4d} | RMSE {rmse:.4f}")

    return mu, bu, bi, P, Q


print("== 训练矩阵分解（k=4）==")
mu, bu, bi, P, Q = train_mf(RATINGS, k=4, epochs=3000)

pred_all = mu + bu[:, None] + bi[None, :] + P @ Q.T
mask = RATINGS > 0
rmse = np.sqrt(np.mean((pred_all[mask] - RATINGS[mask]) ** 2))
mae = np.mean(np.abs(pred_all[mask] - RATINGS[mask]))
print(f"\n训练集 RMSE {rmse:.3f} | MAE {mae:.3f}")

print("\n== 评分预测（前 3 个用户）==")
print("        " + "".join(f"{name:>8s}" for name in ITEM_NAMES))
for u in range(3):
    row = "".join(f"{pred_all[u, i]:8.2f}" for i in range(len(ITEM_NAMES)))
    print(f"  {USER_NAMES[u]:4s}  {row}")

print("\n== 给小明推荐（未看过的物品）==")
u = 0
unseen = np.where(RATINGS[u] == 0)[0]
scored = [(ITEM_NAMES[i], pred_all[u, i]) for i in unseen]
for name, score in sorted(scored, key=lambda x: -x[1]):
    print(f"  {name}: 预测 {score:.2f} 分")

# ---- 潜在因子解释（粗略）----
print("\n== 潜在因子（前 2 维，仅示意）==")
for u, name in enumerate(USER_NAMES):
    print(f"  {name}: ({P[u, 0]:+.2f}, {P[u, 1]:+.2f})")
print("  因子本身没有名字，但相近的用户口味相似")

# ---- 与 User-CF 的对比 ----
print("\n== 矩阵分解 vs User-CF ==")
rows = [
    ("User-CF", "找相似用户加权", "直观、无需训练", "稀疏时相似度不可靠"),
    ("矩阵分解", "学用户/物品向量", "泛化好、预测平滑", "需训练、难解释"),
]
print(f"  {'方法':<10}{'思路':<18}{'优点':<20}{'缺点'}")
for r in rows:
    print(f"  {r[0]:<10}{r[1]:<18}{r[2]:<20}{r[3]}")

# ---- 使用提醒 ----
print("\n== 使用提醒 ==")
for item in [
    "评分要标准化：有人习惯全打 5 分，偏置项能吸收这种差异",
    "正则不能省，否则会过拟合少量评分",
    "隐式反馈（点击/购买）不能直接当评分，需用 BPR/ALS（进阶）",
    "k 通常 8~64，越大越容易过拟合",
    "真实系统用 ALS/SGD 分布式实现，不在单机双重循环",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 把 k 改成 2 和 8，比较 RMSE 与推荐结果。
# 2. 把 lr 改成 0.001，观察收敛速度。
# 3. 用训练出的 Q 计算物品相似度，给小明推荐“相似物品”。
# 4. 思考：矩阵分解为什么能处理“没共同评分”的用户对？
