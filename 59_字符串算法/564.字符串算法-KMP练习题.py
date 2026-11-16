# ===== 第564课：字符串算法-KMP =====
# 知识点：
#   - KMP 核心：前缀函数 π[i] 表示“模式串前 i+1 个字符的最长相等前后缀长度”
#   - 失配时不是回退到起点，而是回退到 π[j-1]，利用已匹配的信息
#   - 预处理 O(m)，匹配 O(n)，总 O(n+m)
#   - π 表的另一个用途：求字符串的最小周期、最长重复前缀
#   - 与第563课暴力法的对比：最坏情况从 O(nm) 降到 O(n+m)
# 依赖：无


def prefix_function(pattern: str) -> list[int]:
    """π[i]：pattern[0..i] 的最长相等真前后缀长度。"""
    m = len(pattern)
    pi = [0] * m
    j = 0
    for i in range(1, m):
        while j > 0 and pattern[i] != pattern[j]:
            j = pi[j - 1]                 # 回退到上一个可能的前缀
        if pattern[i] == pattern[j]:
            j += 1
        pi[i] = j
    return pi


def kmp_search(text: str, pattern: str) -> tuple[list[int], int]:
    """返回 (匹配起点列表, 字符比较次数)。"""
    if not pattern:
        return [], 0
    pi = prefix_function(pattern)
    matches = []
    j = 0                                  # 当前已匹配的模式长度
    comparisons = 0
    for i, ch in enumerate(text):
        while j > 0 and ch != pattern[j]:
            j = pi[j - 1]
        comparisons += 1
        if ch == pattern[j]:
            j += 1
        if j == len(pattern):
            matches.append(i - j + 1)
            j = pi[j - 1]                  # 继续找重叠匹配
    return matches, comparisons


print("== 前缀函数 ==")
for p in ("ababaca", "aabaaab", "abcababc"):
    print(f"  {p:12s} → {prefix_function(p)}")

print("\n== KMP 匹配 ==")
text = "ababcababcabc"
pattern = "abc"
matches, comps = kmp_search(text, pattern)
print(f"  主串：{text}")
print(f"  模式：{pattern}")
print(f"  匹配起点：{matches}")
print(f"  比较次数：{comps}")

# ---- 与暴力法在最坏情况下的对比 ----
print("\n== 最坏情况对比 ==")


def brute_force_search(text, pattern):
    if not pattern:
        return [], 0
    n, m = len(text), len(pattern)
    matches, comparisons = [], 0
    for start in range(n - m + 1):
        j = 0
        while j < m:
            comparisons += 1
            if text[start + j] != pattern[j]:
                break
            j += 1
        if j == m:
            matches.append(start)
    return matches, comparisons


n = 60
text_bad = "a" * n + "b"
pattern_bad = "a" * (n - 1) + "b"
bf_m, bf_c = brute_force_search(text_bad, pattern_bad)
kmp_m, kmp_c = kmp_search(text_bad, pattern_bad)
print(f"  暴力：匹配 {bf_m}，比较 {bf_c} 次")
print(f"  KMP：匹配 {kmp_m}，比较 {kmp_c} 次")
print(f"  比较次数降低约 {bf_c / max(kmp_c, 1):.0f} 倍")

# ---- 找所有重叠匹配 ----
print("\n== 重叠匹配 ==")
print("  text='aaaaa', pattern='aa'")
print("  暴力：", brute_force_search("aaaaa", "aa")[0])
print("  KMP：", kmp_search("aaaaa", "aa")[0])

# ---- π 表的额外用途：最小周期 ----
print("\n== 用 π 表求最小周期 ==")
def min_period(s: str) -> int:
    pi = prefix_function(s)
    n = len(s)
    period = n - pi[-1]
    return period if n % period == 0 else n


for s in ("abcabcabc", "ababab", "abcd", "aaaa"):
    print(f"  {s!r}: π[-1]={prefix_function(s)[-1]}，最小周期={min_period(s)}")

# ---- 复杂度 ----
print("\n== 复杂度 ==")
print("  预处理：O(m)")
print("  匹配：O(n)（j 最多增加 n 次，回退总次数不超过增加次数）")
print("  空间：O(m) 存 π 表")

# ===== 练习题 =====
# 1. 手算 "aabaaab" 的 π 表，再用代码验证。
# 2. 用 KMP 统计 pattern 在 text 中出现的次数（含重叠）。
# 3. 判断字符串是否由某个子串重复构成（用最小周期）。
# 4. 思考：为什么 KMP 的 j 回退总次数是 O(n)？
