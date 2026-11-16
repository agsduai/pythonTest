# ===== 第493课：动态规划专题-最长公共子序列LCS =====
# 知识点：
#   - LCS：两个序列都出现的、顺序一致的子序列（不要求连续）
#   - dp[i][j] = A 前 i 个字符与 B 前 j 个字符的 LCS 长度
#   - 转移：字符相同 → dp[i-1][j-1] + 1；不同 → max(dp[i-1][j], dp[i][j-1])
#   - 重建：从右下角回溯，相同字符就收集
#   - 应用：diff 工具、DNA 比对、版本对比、编辑距离（第387课）的基础
#   - 与第387课编辑距离的区别：LCS 只允许“保留”，编辑距离允许增删改
# 依赖：无


def lcs(a: str, b: str):
    """返回 (LCS 长度, LCS 字符串, dp 表)。"""
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    # 回溯
    i, j, chars = m, n, []
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            chars.append(a[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1

    return dp[m][n], "".join(reversed(chars)), dp


A = "ABCBDAB"
B = "BDCABA"
length, seq, dp = lcs(A, B)
print("== 输入 ==")
print(f"  A = {A}")
print(f"  B = {B}")
print(f"\n  最长公共子序列长度：{length}")
print(f"  一个 LCS：{seq}")
print("  （可能有多个等长解，回溯方向决定取哪一个）")

# ---- 打印 dp 表 ----
print("\n== dp 表（行=A 的前缀，列=B 的前缀）==")
print("      " + "".join(f"{c:>3s}" for c in ["_"] + list(B)))
for i, row in enumerate(dp):
    label = "_" if i == 0 else A[i - 1]
    print(f"  {label:3s}" + "".join(f"{v:>3d}" for v in row))

# ---- 应用 1：diff 的“保留部分” ----
print("\n== 应用：文本对比 ==")
old = ["def", "add", "(", "a", ",", "b", ")", ":", "return", "a", "+", "b"]
new = ["def", "add", "(", "a", ",", "b", ")", ":", "return", "a", "+", "b", "+", "1"]
length2, common, _ = lcs(old, new)
print(f"  旧版本 {len(old)} 个 token，新版本 {len(new)} 个")
print(f"  公共部分 {length2} 个：", common.split("\x00") if False else common)

# 用字符级 LCS 模拟 diff 的“保留/新增”
old_text = "kitten"
new_text = "sitting"
length3, common3, _ = lcs(old_text, new_text)
print(f"\n  '{old_text}' vs '{new_text}'")
print(f"  LCS = '{common3}'（长度 {length3}）")
print("  编辑距离（第387课）= 3：k→s、e→i、插入 g")

# ---- 应用 2：判断是否为子序列 ----
print("\n== 应用：判断子序列 ==")
def is_subsequence(s, t):
    it = iter(t)
    return all(ch in it for ch in s)

for s in ("abc", "acb"):
    print(f"  '{s}' 是 'ahbgdc' 的子序列：{is_subsequence(s, 'ahbgdc')}")

# ---- 空间优化 ----
print("\n== 空间优化 ==")
def lcs_length_1d(a, b):
    """只求长度：两行滚动即可。"""
    prev = [0] * (len(b) + 1)
    for ca in a:
        cur = [0] * (len(b) + 1)
        for j, cb in enumerate(b, 1):
            if ca == cb:
                cur[j] = prev[j - 1] + 1
            else:
                cur[j] = max(prev[j], cur[j - 1])
        prev = cur
    return prev[-1]


print("  一维滚动结果：", lcs_length_1d(A, B), "（与二维一致）")
print("  只求长度 O(min(m,n)) 空间；重建方案仍需二维表或额外索引")

# ---- 变体 ----
print("\n== 常见变体 ==")
for item in [
    "最长公共子串（连续）：字符不同时 dp[i][j]=0",
    "最短公共超序列：长度 = m+n-LCS",
    "编辑距离：把“不匹配”扩展为增/删/改三种操作",
    "多个序列的 LCS：维度增加，复杂度指数上升",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 实现“最长公共子串”（连续），返回子串与长度。
# 2. 用 LCS 求两个字符串的“最短公共超序列”。
# 3. 输出所有等长的 LCS（可能不止一个）。
# 4. 思考：LCS 回溯时为什么“相等就一定要收集”？
