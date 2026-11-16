# ===== 第855课：生物信息学与序列算法-SmithWaterman局部比对 =====
# 知识点：
#   - 局部比对：只对齐两条序列中最相似的一段，其余部分不参与
#   - Smith-Waterman = NW 加一条规则：dp 值不允许为负（负值归零 = 随时重开）
#   - 回溯从最大值格子开始，走到 0 为止
#   - 适用：找出共同 motif/结构域、跨物种的保守片段、部分同源
#   - 同一对序列：全局比分「整体」，局部比分「片段」——得分不可直接比较
# 依赖：无（标准库）


def smith_waterman(a, b, match=2, mismatch=-1, gap=-2):
    """局部比对 -> (得分, 对齐A, 对齐B, 标记行, 终点(i,j))。"""
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    best, bi, bj = 0, 0, 0
    for i in range(1, n + 1):
        ai = a[i - 1]
        for j in range(1, m + 1):
            s = match if ai == b[j - 1] else mismatch
            dp[i][j] = max(0,
                           dp[i - 1][j - 1] + s,
                           dp[i - 1][j] + gap,
                           dp[i][j - 1] + gap)
            if dp[i][j] > best:
                best, bi, bj = dp[i][j], i, j
    i, j = bi, bj
    ra, rb, marks = [], [], []
    while i > 0 and j > 0 and dp[i][j] > 0:
        s = match if a[i - 1] == b[j - 1] else mismatch
        if dp[i][j] == dp[i - 1][j - 1] + s:
            ra.append(a[i - 1]); rb.append(b[j - 1])
            marks.append("|" if a[i - 1] == b[j - 1] else " ")
            i -= 1; j -= 1
        elif dp[i][j] == dp[i - 1][j] + gap:
            ra.append(a[i - 1]); rb.append("-"); marks.append(" ")
            i -= 1
        else:
            ra.append("-"); rb.append(b[j - 1]); marks.append(" ")
            j -= 1
    return (best, "".join(reversed(ra)), "".join(reversed(rb)),
            "".join(reversed(marks)), (i, j), (bi, bj))


print("== 共同 motif 的局部比对 ==")
a = "TTACGGCATCGATTACGATC"
b = "GGCCATCGAGGCTTACGGA"
score, ra, rb, marks, start, end = smith_waterman(a, b)
print(f"  A = {a}")
print(f"  B = {b}")
print(f"  最高得分 = {score}，对齐落在 A[{start[0]}:{end[0]}) 与 B[{start[1]}:{end[1]})")
print(f"  局部对齐A: {ra}")
print(f"           {marks}")
print(f"  局部对齐B: {rb}")

print("\n== 同一对序列：局部 vs 全局 ==")


def needleman_score(a, b, match=2, mismatch=-1, gap=-2):
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = i * gap
    for j in range(1, m + 1):
        dp[0][j] = j * gap
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            s = match if a[i - 1] == b[j - 1] else mismatch
            dp[i][j] = max(dp[i - 1][j - 1] + s, dp[i - 1][j] + gap, dp[i][j - 1] + gap)
    return dp[n][m]


g_score = needleman_score(a, b)
print(f"  全局得分 = {g_score}（强行对齐首尾，被两端大段差异拖累）")
print(f"  局部得分 = {score}（只保留最相似片段）")
print("  两者语义不同：全局比较整体同源，局部比较功能片段")

print("\n== 短序列包含关系 ==")
s3, r1, r2, mk, st3, en3 = smith_waterman("CATCGA", "AAACATCGAGGG", 2, -1, -2)
print(f"  在 12bp 序列中找 6bp 子串: 得分={s3} 对齐=[{st3[1]}:{en3[1]}) -> {r2}")
print("  完全包含的子串得到满分（每列 match=2）")

print("\n== 打分参数的影响 ==")
pair = ("ACGTCAGCT", "AGGTCGACCT")
for match, mismatch, gap in ((2, -1, -2), (3, -2, -3), (1, -1, -1)):
    sc, x1, x2, mkx, _, _ = smith_waterman(*pair, match, mismatch, gap)
    print(f"  match={match} mismatch={mismatch} gap={gap}"
          f" -> 得分 {sc:>3}  一致 {mkx.count('|'):>2}  对齐长 {len(mkx)}")
print("  参数越宽松（错配/空位罚得越轻），局部对齐越长")

print("\n== 负值归零的意义 ==")
print("  dp[i][j] = max(0, 三种延伸)")
print("  - 延伸收益 < 0 时归零：相当于「从这里重新开始」")
print("  - 回溯止于 0：自然截断出局部最优片段，无需预先知道片段长度")
print("  - 与 NW 唯一的算法差异就是这一行 max(0, ...)")

print("\n== 小结 ==")
for line in (
    "  局部比对 = NW + 「不允许负分」一条规则",
    "  回溯从全局最大格子出发，止于任意 0 格子",
    "  找 motif/保守域/部分同源用局部；比较全长同源用全局",
    "  856 课：O(n×m) 对完整数据库太慢 -> 用 k-mer 种子先粗筛",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 输出全部得分 ≥ 阈值的局部对齐（提示：把已回溯区域在 DP 矩阵中屏蔽后重复找最大值）。
# 2. 实现重复 motif 检测：一条序列与自身做局部比对，找出两次以上出现的 motif。
# 3. 给 Smith-Waterman 加线性空位计分统计：分别统计 match/mismatch/gap 数量。
# 4. 思考：什么场景下全局比对得分反而高于局部比对？两者的分数量纲为什么不可比？
