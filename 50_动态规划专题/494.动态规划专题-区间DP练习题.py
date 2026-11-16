# ===== 第494课：动态规划专题-区间DP =====
# 知识点：
#   - 区间 DP：状态定义在“区间 [i, j]”上，按区间长度从小到大递推
#   - 经典题 1：最长回文子序列（LPS）= 原串与反转串的 LCS，也可直接区间 DP
#   - 经典题 2：最少插入次数构成回文 = n - LPS
#   - 转移：s[i]==s[j] → dp[i][j] = dp[i+1][j-1] + 2
#           否则 → max(dp[i+1][j], dp[i][j-1])
#   - 遍历顺序：先枚举长度，再枚举起点（保证子区间先算好）
#   - 与第387课编辑距离、第493课 LCS 的关系
# 依赖：无


def longest_palindromic_subsequence(s: str):
    """返回 (长度, 具体的回文子序列, dp 表)。"""
    n = len(s)
    if n == 0:
        return 0, "", []
    dp = [[0] * n for _ in range(n)]
    for i in range(n):
        dp[i][i] = 1

    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                dp[i][j] = dp[i + 1][j - 1] + 2 if length > 2 else 2
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])

    # 重建：先收集左半部分与中间字符
    i, j, left, mid = 0, n - 1, [], ""
    while i <= j:
        if i == j:
            mid = s[i]
            break
        if s[i] == s[j]:
            left.append(s[i])
            i += 1
            j -= 1
        elif dp[i + 1][j] >= dp[i][j - 1]:
            i += 1
        else:
            j -= 1
    palindrome = "".join(left) + mid + "".join(reversed(left))
    return dp[0][n - 1], palindrome, dp


print("== 最长回文子序列 ==")
for s in ("bbbab", "cbbd", "abcba", "character"):
    length, seq, _ = longest_palindromic_subsequence(s)
    print(f"  {s:10s} → 长度 {length}，序列 {seq!r}")

# ---- 打印一个 dp 表 ----
s = "bbbab"
_, _, dp = longest_palindromic_subsequence(s)
print(f"\n== dp 表（{s}）==")
print("      " + "".join(f"{c:>3s}" for c in s))
for i, row in enumerate(dp):
    print(f"  {s[i]}  " + "".join(f"{v:>3d}" for v in row))
print("  只填了上三角：dp[i][j] 表示 s[i..j] 的 LPS 长度")

# ---- 应用：最少插入次数构成回文 ----
print("\n== 最少插入次数构成回文 ==")
for s in ("abc", "abcd", "racecar"):
    length, _, _ = longest_palindromic_subsequence(s)
    print(f"  {s:8s} 长度 {len(s)}，LPS {length} → 最少插入 {len(s) - length} 次")

# ---- 与 LCS 的关系：LPS(s) = LCS(s, reverse(s)) ----
print("\n== LPS 与 LCS 的关系 ==")
def lcs_length(a, b):
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[m][n]


for s in ("bbbab", "character"):
    lps_len, _, _ = longest_palindromic_subsequence(s)
    lcs_len = lcs_length(s, s[::-1])
    print(f"  {s}: LPS={lps_len}，LCS(s, 反转)={lcs_len}，一致={lps_len == lcs_len}")

# ---- 另一道区间 DP：戳气球（思路示意）----
print("\n== 区间 DP 模板（戳气球/矩阵链乘）==")
print("  dp[i][j] = 只考虑区间 (i,j) 内元素的最优值")
print("  枚举最后一个操作 k：dp[i][j] = max(dp[i][k] + dp[k][j] + 收益(i,k,j))")
for item in [
    "矩阵链乘：合并顺序影响总代价",
    "戳气球：最后戳破 k，左右区间独立",
    "石子合并：最后一次合并把两堆并成一堆",
    "共同点：先算小区间，再算大区间",
]:
    print("  -", item)

# ---- 遍历顺序对比 ----
print("\n== 为什么必须先枚举长度？==")
print("  dp[i][j] 依赖 dp[i+1][j]、dp[i][j-1]、dp[i+1][j-1]（更短的区间）")
print("  如果按 i 从 0 到 n 遍历，dp[i+1][j] 还没算出来 → 结果错")
print("  按长度从 2 到 n 枚举，保证所有短区间先完成")

# ===== 练习题 =====
# 1. 实现“最长回文子串”（连续），对比子序列的差别。
# 2. 用区间 DP 实现“石子合并”最小代价。
# 3. 输出所有最长回文子序列（可能多个）。
# 4. 思考：区间 DP 与分治（第249课）的相似与不同。
