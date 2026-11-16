# ===== 第387课：文本处理与搜索-编辑距离与拼写纠错 =====
# 知识点：
#   - 编辑距离（Levenshtein）：插入/删除/替换一个字符记 1 次，最少几次能改到目标
#   - 动态规划：dp[i][j] = 前 i 个字符与前 j 个字符的最小编辑距离
#   - 转移：字符相同取左上；不同取 min(左、上、左上) + 1
#   - 拼写纠错：在词表里找距离最小的候选（可加长度差剪枝）
#   - 与第255课 DP 三要素一脉相承
# 依赖：无


def edit_distance(a: str, b: str) -> int:
    """经典二维 DP。返回最少编辑次数。"""
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i                  # 全删除
    for j in range(n + 1):
        dp[0][j] = j                  # 全插入

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]          # 字符相同，不用操作
            else:
                dp[i][j] = min(
                    dp[i - 1][j] + 1,                # 删除
                    dp[i][j - 1] + 1,                # 插入
                    dp[i - 1][j - 1] + 1,            # 替换
                )
    return dp[m][n]


# ---- 基础示例 ----
pairs = [("kitten", "sitting"), ("flaw", "lawn"), ("python", "python"), ("", "abc")]
for a, b in pairs:
    print(f"edit_distance({a!r}, {b!r}) = {edit_distance(a, b)}")

# ---- 打印短字符串的 DP 表，直观理解转移 ----
def show_table(a: str, b: str):
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    print(f"\nDP 表（{a} → {b}）：")
    print("     " + "  ".join(["_"] + list(b)))
    for i, row in enumerate(dp):
        label = a[i - 1] if i > 0 else "_"
        print(f"  {label}  " + "  ".join(str(v) for v in row))


show_table("cat", "cut")

# ---- 拼写纠错器 ----
VOCAB = ["python", "pandas", "numpy", "matplotlib", "function", "variable",
         "dictionary", "list", "tuple", "index", "search", "machine"]


def suggest(word: str, vocab=VOCAB, max_dist: int = 2) -> list[tuple[str, int]]:
    """返回距离 <= max_dist 的候选，按距离升序。"""
    word = word.lower()
    candidates = []
    for cand in vocab:
        if abs(len(cand) - len(word)) > max_dist:      # 长度差剪枝
            continue
        d = edit_distance(word, cand)
        if d <= max_dist:
            candidates.append((cand, d))
    return sorted(candidates, key=lambda x: x[1])


print("\n拼写建议：")
for wrong in ["pyhton", "panda", "numpyy", "dictonary", "zzzzzz"]:
    result = suggest(wrong)
    print(f"  {wrong:10s} → {result if result else '（无候选，建议人工确认）'}")

# 自动纠正：只接受距离最小的唯一候选
def autocorrect(word: str) -> str:
    cands = suggest(word)
    if not cands:
        return word
    best_dist = cands[0][1]
    best = [c for c, d in cands if d == best_dist]
    return best[0] if len(best) == 1 else word    # 多个并列则不擅自改


print("\n自动纠正：", {w: autocorrect(w) for w in ["pyhton", "panda", "listt"]})

# ===== 练习题 =====
# 1. 实现“只允许替换”的距离（汉明距离），对比与本课结果差异。
# 2. 把 suggest 的候选扩展到“键盘相邻键位”（如 pyhton→python 的换位）。
# 3. 用第383课的词频给候选加权：距离相同选更常用的词。
# 4. 思考：编辑距离 O(mn) 的成本，处理百万词表时如何优化？（提示：BK 树）
