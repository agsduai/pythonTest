# ===== 第854课：生物信息学与序列算法-Needleman-Wunsch全局比对 =====
# 知识点：
#   - 序列比对 = 把两条序列按最佳对应排在一起，量化相似性
#   - 打分：匹配加分、错配罚分、空位（gap）罚分
#   - Needleman-Wunsch 全局比对：从头到尾对齐，DP 矩阵 O(n×m)
#   - dp[i][j] = max(对角 + 匹配分, 上 + gap, 左 + gap)，回溯得对齐结果
#   - LCS（491 课）是 NW 在 match=1/mismatch=-inf 下的特例
# 依赖：无（标准库）


def needleman_wunsch(a, b, match=1, mismatch=-1, gap=-2):
    """全局比对 -> (得分, 对齐A, 对齐B, 标记行)。"""
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    tb = [[None] * (m + 1) for _ in range(n + 1)]     # D/U/L
    for i in range(1, n + 1):
        dp[i][0] = i * gap
        tb[i][0] = "U"
    for j in range(1, m + 1):
        dp[0][j] = j * gap
        tb[0][j] = "L"
    for i in range(1, n + 1):
        ai = a[i - 1]
        row = dp[i]
        prev = dp[i - 1]
        for j in range(1, m + 1):
            s = match if ai == b[j - 1] else mismatch
            best = ("D", prev[j - 1] + s)
            if prev[j] + gap > best[1]:
                best = ("U", prev[j] + gap)
            if row[j - 1] + gap > best[1]:
                best = ("L", row[j - 1] + gap)
            tb[i][j], row[j] = best
    i, j = n, m
    ra, rb, marks = [], [], []
    while i > 0 or j > 0:
        d = tb[i][j]
        if d == "D":
            same = a[i - 1] == b[j - 1]
            ra.append(a[i - 1]); rb.append(b[j - 1]); marks.append("|" if same else " ")
            i -= 1; j -= 1
        elif d == "U":
            ra.append(a[i - 1]); rb.append("-"); marks.append(" ")
            i -= 1
        else:
            ra.append("-"); rb.append(b[j - 1]); marks.append(" ")
            j -= 1
    return (dp[n][m], "".join(reversed(ra)), "".join(reversed(rb)),
            "".join(reversed(marks)))


def show_alignment(score, ra, rb, marks, width=50):
    print(f"  得分 = {score}，长度 = {len(ra)}")
    for s in range(0, len(ra), width):
        print(f"  A {ra[s:s + width]}")
        print(f"    {marks[s:s + width]}")
        print(f"  B {rb[s:s + width]}")


print("== 小例子：两条相近序列 ==")
a, b = "ACACACTA", "AGCACACA"
score, ra, rb, marks = needleman_wunsch(a, b)
print(f"  A = {a}\n  B = {b}")
show_alignment(score, ra, rb, marks)
ident = marks.count("|") / len(marks)
print(f"  一致率 = {marks.count('|')}/{len(marks)} = {ident:.0%}")

print("\n== 手算对照：ACG vs ACG ==")
score2, ra2, rb2, mk2 = needleman_wunsch("ACG", "ACG")
show_alignment(score2, ra2, rb2, mk2)
print("  3 个匹配 + 0 空位 = 3 分")

print("\n== 打分参数改变比对结果 ==")
pair = ("GATTACA", "GCATGCU")
for match, mismatch, gap in ((1, -1, -2), (2, -1, -1), (1, -3, 0), (1, 0, -1)):
    s, r1, r2, mk = needleman_wunsch(pair[0], pair[1], match, mismatch, gap)
    print(f"  match={match} mismatch={mismatch} gap={gap:>2}"
          f" -> 得分 {s:>3}  一致 {mk.count('|')}  gap {r1.count('-') + r2.count('-')}")
print("  gap 罚分重 -> 少开空位、多错配；gap 罚分轻 -> 多开空位")

print("\n== DP 矩阵（GATT vs GCAT，小规模展示）==")


def print_dp(a, b, match=1, mismatch=-1, gap=-2):
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
    print(f"        " + "  ".join(f"{c:>3}" for c in "-" + b))
    for i in range(n + 1):
        print(f"    {(a[i - 1] if i else '-'):>3}  " + "  ".join(f"{dp[i][j]:>3}" for j in range(m + 1)))


print_dp("GATT", "GCAT")
print("  右下角 = 全局比对得分")

print("\n== 与 LCS 的关系 ==")
s3, r1, r2, mk = needleman_wunsch("ABCBDAB", "BDCABA", 1, -10, -10)
print(f"  极重错配/空位罚分下，最优对齐只保留 LCS 匹配：标记数 = {mk.count('|')}（LCS('ABCBDAB','BDCABA') = 4）")

print("\n== 小结 ==")
for line in (
    "  全局比对适合长度相近、整体同源的序列",
    "  DP 矩阵每个格子只依赖左、上、左上 -> O(n×m) 时间与空间",
    "  打分体系是生物学假设的编码：参数变了结论就变",
    "  855 课：只对齐最相似片段的局部比对 Smith-Waterman",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「记分矩阵」版本：用 dict 给不同碱基对不同的错配罚分（如 transitions
#    A<->G 宽松、transversions 严格），观察比对变化。
# 2. 统计比对结果中的 match/mismatch/gap 三类数量并输出统计行。
# 3. 实现线性空间版本（Hirschberg 或滚动数组 + 分治回溯），把空间降到 O(min(n,m))。
# 4. 思考：为什么全局比对中「最优对齐」可能不止一个？如何枚举多个等分对齐？
