# ===== 第477课：AB测试与统计-假设检验与p值 =====
# 知识点：
#   - 假设检验：先假设“没有差异”（原假设 H0），看数据是否足以推翻它
#   - p 值：在 H0 为真的前提下，出现“当前或更极端结果”的概率
#   - 显著性水平 α（常用 0.05）：p < α 才拒绝 H0
#   - p 值不是“H0 为真的概率”，也不是“效果大小”
#   - 置换检验（permutation test）：打乱分组标签，构造 H0 下的分布，不依赖公式
#   - 与第476课置信区间互补：区间看“效果范围”，检验看“是否显著”
# 依赖：无（random / statistics）

import random
import statistics

random.seed(2026)


# ---------------- 置换检验 ----------------
def permutation_test(control, treatment, n_perm=5000):
    """H0：两组来自同一分布。返回观测差异与双侧 p 值。"""
    observed = statistics.mean(treatment) - statistics.mean(control)
    combined = control + treatment
    n_c = len(control)
    count = 0
    diffs = []
    for _ in range(n_perm):
        shuffled = combined[:]
        random.shuffle(shuffled)
        new_c = shuffled[:n_c]
        new_t = shuffled[n_c:]
        diff = statistics.mean(new_t) - statistics.mean(new_c)
        diffs.append(diff)
        if abs(diff) >= abs(observed):
            count += 1
    p_value = count / n_perm
    return observed, p_value, sorted(diffs)


# ---- 场景 1：两组几乎没差异 ----
control = [random.gauss(10, 2) for _ in range(100)]
treatment = [random.gauss(10.1, 2) for _ in range(100)]
diff, p, dist = permutation_test(control, treatment)
print("== 场景 1：几乎无差异 ==")
print(f"  观测差异：{diff:+.3f}")
print(f"  置换分布：均值 {statistics.mean(dist):+.3f}，95% 范围 "
      f"[{dist[int(0.025 * len(dist))]:+.3f}, {dist[int(0.975 * len(dist))]:+.3f}]")
print(f"  p 值：{p:.4f} → {'显著' if p < 0.05 else '不显著（不能拒绝 H0）'}")

# ---- 场景 2：有明显差异 ----
control2 = [random.gauss(10, 2) for _ in range(100)]
treatment2 = [random.gauss(11.5, 2) for _ in range(100)]
diff2, p2, dist2 = permutation_test(control2, treatment2)
print("\n== 场景 2：明显差异 ==")
print(f"  观测差异：{diff2:+.3f}")
print(f"  p 值：{p2:.4f} → {'显著' if p2 < 0.05 else '不显著'}")

# ---- 场景 3：差异小但样本大 ----
control3 = [random.gauss(10, 2) for _ in range(5000)]
treatment3 = [random.gauss(10.2, 2) for _ in range(5000)]
diff3, p3, _ = permutation_test(control3, treatment3, n_perm=1000)
print("\n== 场景 3：微小差异 + 大样本 ==")
print(f"  观测差异：{diff3:+.3f}")
print(f"  p 值：{p3:.4f} → {'显著' if p3 < 0.05 else '不显著'}")
print("  提醒：显著 ≠ 重要。大样本下 0.2 的差异也可能显著，要看业务价值")

# ---- p 值的可视化（文本）----
print("\n== 置换分布直方图（场景 2）==")
lo, hi = min(dist2), max(dist2)
bins = 20
step = (hi - lo) / bins or 1
counts = [0] * bins
for d in dist2:
    idx = min(bins - 1, int((d - lo) / step))
    counts[idx] += 1
peak = max(counts)
for i, c in enumerate(counts):
    left = lo + i * step
    bar = "█" * int(c / peak * 30)
    marker = " ← 观测值" if left <= diff2 < left + step else ""
    print(f"  {left:+.2f} | {bar}{marker}")

# ---- 双侧 vs 单侧 ----
print("\n== 单侧/双侧 ==")
print("  双侧：只关心“有没有差异”（默认，A/B 测试常用）")
print("  单侧：事先就假设“只可能更好”，需要更强的事前理由")
print("  本课 p 值均为双侧（|diff| >= |observed|）")

# ---- 使用清单 ----
print("\n== 假设检验清单 ==")
for item in [
    "先定 α、样本量、指标，再看数据（避免 p-hacking）",
    "p < 0.05 ≠ 一定有业务价值，要结合效应量与置信区间",
    "多重比较要校正（第481课）",
    "检验假设不满足时（严重偏态/小样本），优先 Bootstrap/置换",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 把置换次数改成 200 和 20000，观察 p 值的稳定性。
# 2. 实现单侧置换检验（只统计 diff >= observed）。
# 3. 用同样的数据计算效应量 Cohen's d，对比 p 值结论。
# 4. 思考：为什么“先看数据再定假设”会让 p 值失去意义？
