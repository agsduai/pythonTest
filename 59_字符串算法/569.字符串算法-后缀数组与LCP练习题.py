# ===== 第569课：字符串算法-后缀数组与LCP =====
# 知识点：
#   - 后缀数组 SA：把字符串的所有后缀按字典序排序后的起始下标
#   - 暴力构建 O(n² log n)（排序 + 字符串比较），本课用它讲清概念
#   - LCP 数组：相邻后缀的最长公共前缀长度（Kasai 算法 O(n)）
#   - 用途：最长重复子串、不同子串计数、字符串相似度、全文索引
#   - 与第419课 Trie 的区别：后缀数组更省空间，适合长文本
#   - 生产级构建用倍增/SA-IS，O(n log n) 或 O(n)
# 依赖：无


def build_suffix_array(s: str) -> list[int]:
    """暴力版：直接按后缀字符串排序（便于理解）。"""
    return sorted(range(len(s)), key=lambda i: s[i:])


def build_lcp(s: str, sa: list[int]) -> list[int]:
    """Kasai 算法：lcp[k] = LCP(sa[k-1], sa[k])。"""
    n = len(s)
    rank = [0] * n
    for i, pos in enumerate(sa):
        rank[pos] = i

    lcp = [0] * n
    h = 0
    for i in range(n):
        if rank[i] > 0:
            j = sa[rank[i] - 1]
            while i + h < n and j + h < n and s[i + h] == s[j + h]:
                h += 1
            lcp[rank[i]] = h
            if h > 0:
                h -= 1
    return lcp


def longest_repeated_substring(s: str):
    sa = build_suffix_array(s)
    lcp = build_lcp(s, sa)
    best_len = max(lcp) if lcp else 0
    if best_len == 0:
        return "", 0
    idx = lcp.index(best_len)
    start = sa[idx]
    return s[start:start + best_len], best_len


s = "banana"
sa = build_suffix_array(s)
lcp = build_lcp(s, sa)

print("== 后缀数组 ==")
print(f"  字符串：{s!r}")
print(f"  {'排名':<4}{'起点':<6}{'后缀':<12}{'LCP'}")
for rank, pos in enumerate(sa):
    print(f"  {rank:<4}{pos:<6}{s[pos:]!r:<12}{lcp[rank]}")

print("\n== 最长重复子串 ==")
for word in ("banana", "mississippi", "abracadabra", "abcd"):
    sub, length = longest_repeated_substring(word)
    print(f"  {word!r} → {sub!r}（长度 {length}）")

# ---- 不同子串计数 ----
print("\n== 不同子串数量 ==")
def distinct_substrings(s: str) -> int:
    n = len(s)
    sa = build_suffix_array(s)
    lcp = build_lcp(s, sa)
    return n * (n + 1) // 2 - sum(lcp)


for word in ("banana", "aaaa", "abc"):
    print(f"  {word!r}: {distinct_substrings(word)} 个不同子串")

# ---- LCP 的性质 ----
print("\n== LCP 的意义 ==")
print("  lcp[k] 是排序后第 k 与第 k-1 个后缀的最长公共前缀")
print("  最大 LCP 对应“最长重复子串”")
print("  sum(LCP) 是所有后缀的重复部分，可用于减去重复子串")

# ---- 暴力构建的复杂度 ----
print("\n== 复杂度 ==")
print("  暴力 SA：O(n² log n)（每个后缀是 O(n) 字符串，排序比较 O(n)）")
print("  Kasai LCP：O(n)")
print("  生产：倍增法 O(n log n)，SA-IS O(n)")
print("  n=1 万时暴力可能几秒；n=100 万必须用 O(n log n) 算法")

# ---- 与后缀自动机/后缀树的对比 ----
print("\n== 相关结构 ==")
rows = [
    ("后缀数组 + LCP", "空间小、实现适中", "重复子串、子串计数"),
    ("后缀树", "查询强、构建复杂", "生物信息、复杂模式"),
    ("后缀自动机", "O(n) 构建、状态少", "子串统计、最长公共子串"),
    ("Trie", "前缀查询强", "词典、自动补全（第419课）"),
]
print(f"  {'结构':<16}{'特点':<24}{'典型用途'}")
for r in rows:
    print(f"  {r[0]:<16}{r[1]:<24}{r[2]}")

# ===== 练习题 =====
# 1. 输出所有长度 >= 2 的重复子串（按 LCP 分组）。
# 2. 求两个字符串的最长公共子串（拼接 + 分隔符 + 后缀数组）。
# 3. 用 SA 实现“子串查找”：二分查找后缀数组。
# 4. 思考：为什么后缀数组排序后，相邻后缀的 LCP 最大？
