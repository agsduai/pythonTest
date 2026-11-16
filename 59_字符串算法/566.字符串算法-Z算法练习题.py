# ===== 第566课：字符串算法-Z算法 =====
# 知识点：
#   - Z[i]：从位置 i 开始的后缀与整个字符串的最长公共前缀长度
#   - 维护最右匹配区间 [l, r]，利用“镜像位置”复用已算结果
#   - 模式匹配：pattern + '#' + text，Z[i] >= len(pattern) 的位置就是匹配
#   - 复杂度 O(n+m)，代码比 KMP 短
#   - '#' 必须是两个串中都不出现的字符（或用一个不冲突的分隔符）
#   - 与 KMP 的共同点：都在利用“已匹配的信息”
# 依赖：无


def z_function(s: str) -> list[int]:
    n = len(s)
    z = [0] * n
    l = r = 0
    for i in range(1, n):
        if i <= r:
            z[i] = min(r - i + 1, z[i - l])   # 镜像复用
        while i + z[i] < n and s[z[i]] == s[i + z[i]]:
            z[i] += 1
        if i + z[i] - 1 > r:                  # 扩展最右区间
            l, r = i, i + z[i] - 1
    return z


print("== Z 数组 ==")
for s in ("aabcaabxaaaz", "abacaba", "aaaaa"):
    print(f"  {s:14s} → {z_function(s)}")

print("\n== 模式匹配 ==")
def z_search(text: str, pattern: str, sep: str = "\x00") -> list[int]:
    if not pattern:
        return []
    combined = pattern + sep + text
    z = z_function(combined)
    m = len(pattern)
    return [i - m - 1 for i in range(m + 1, len(combined)) if z[i] >= m]


text = "ababcababcabc"
pattern = "abc"
print(f"  主串：{text}")
print(f"  模式：{pattern}")
print(f"  匹配起点：{z_search(text, pattern)}")

# ---- 逐步观察 Z 的计算 ----
print("\n== 逐步计算（abacaba）==")
s = "abacaba"
z = z_function(s)
for i in range(len(s)):
    print(f"  i={i} 字符 {s[i]!r}：z={z[i]}（后缀 {s[i:]!r} 与整体公共前缀）")

# ---- 与 KMP 对比 ----
print("\n== 与 KMP 对比 ==")
def kmp_search(text, pattern):
    if not pattern:
        return []
    pi = [0] * len(pattern)
    j = 0
    for i in range(1, len(pattern)):
        while j and pattern[i] != pattern[j]:
            j = pi[j - 1]
        if pattern[i] == pattern[j]:
            j += 1
        pi[i] = j

    res = []
    j = 0
    for i, ch in enumerate(text):
        while j and ch != pattern[j]:
            j = pi[j - 1]
        if ch == pattern[j]:
            j += 1
        if j == len(pattern):
            res.append(i - j + 1)
            j = pi[j - 1]
    return res


for t, p in [("aaaaa", "aa"), ("ababc", "abc"), ("xyz", "a")]:
    assert z_search(t, p) == kmp_search(t, p)
print("  5 组用例与 KMP 结果一致")

# ---- Z 数组的其他用途 ----
print("\n== Z 数组的用途 ==")
print("  1. 模式匹配（本课）")
print("  2. 求字符串的最小周期：最小的 i 使 i+z[i]==n 且 n%i==0")
print("  3. 统计每个前缀出现次数（z 值累加）")
print("  4. 最长公共前后缀")

# ---- 分隔符的坑 ----
print("\n== 分隔符的坑 ==")
print("  pattern + '#' + text：如果 '#' 在串中出现，会误判")
print("  解决：用不会出现的字符（如 \\x00），或先检查字符集")
try:
    print("  反例：", z_search("a#b", "a", sep="#"))
except Exception as exc:
    print("  ", exc)

# ---- 复杂度 ----
print("\n== 复杂度 ==")
print("  时间 O(n+m)，空间 O(n+m)（拼接串 + Z 数组）")
print("  比 KMP 多存一个拼接串，但代码更短、更不易写错")

# ===== 练习题 =====
# 1. 用 Z 数组求 "abcabcabc" 的最小周期。
# 2. 统计每个前缀在原串中出现的次数（提示：z 值 + 后缀计数）。
# 3. 实现“只匹配一次”的版本，找到即返回。
# 4. 思考：Z 算法与 KMP 的 π 表有什么对应关系？
