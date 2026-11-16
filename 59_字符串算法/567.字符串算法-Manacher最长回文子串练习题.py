# ===== 第567课：字符串算法-Manacher最长回文子串 =====
# 知识点：
#   - 暴力枚举中心：O(n²)；Manacher 利用回文对称性做到 O(n)
#   - 统一奇偶：在字符间插入 #，所有回文都变成奇数长度
#   - 维护最右回文边界 [center, right]，用镜像位置复用半径
#   - p[i] 表示以 i 为中心的回文半径；最长回文长度 = max(p)
#   - 与第494课区间 DP 求回文子序列的区别：这里求“连续子串”
#   - 与第564课 KMP 的共同思想：利用已计算的信息避免重复
# 依赖：无


def longest_palindrome(s: str) -> tuple[str, int, int]:
    """返回 (最长回文子串, 起始下标, 长度)。"""
    if not s:
        return "", 0, 0

    # 插入分隔符，首尾加哨兵，避免边界判断
    t = "^#" + "#".join(s) + "#$"
    n = len(t)
    p = [0] * n
    center = right = 0

    for i in range(1, n - 1):
        mirror = 2 * center - i
        if i < right:
            p[i] = min(right - i, p[mirror])
        # 向两侧扩展
        while t[i + p[i] + 1] == t[i - p[i] - 1]:
            p[i] += 1
        if i + p[i] > right:
            center, right = i, i + p[i]

    max_len = max(p)
    center_index = p.index(max_len)
    start = (center_index - max_len) // 2
    return s[start:start + max_len], start, max_len


print("== 最长回文子串 ==")
for s in ("babad", "cbbd", "forgeeksskeegfor", "a", "abacdfgdcaba", "aaaa"):
    sub, start, length = longest_palindrome(s)
    print(f"  {s:20s} → {sub!r}（起点 {start}，长度 {length}）")

# ---- 与暴力法对比 ----
print("\n== 暴力法对照 ==")
def brute_longest(s: str) -> str:
    best = ""
    n = len(s)
    for i in range(n):
        for j in range(i + 1, n + 1):
            piece = s[i:j]
            if piece == piece[::-1] and len(piece) > len(best):
                best = piece
    return best


for s in ("babad", "cbbd", "aaaa"):
    print(f"  {s!r}: Manacher={longest_palindrome(s)[0]!r}，暴力={brute_longest(s)!r}")

# ---- 观察 p 数组 ----
print("\n== p 数组（abacaba）==")
s = "abacaba"
t = "^#" + "#".join(s) + "#$"
n = len(t)
p = [0] * n
c = r = 0
for i in range(1, n - 1):
    mirror = 2 * c - i
    if i < r:
        p[i] = min(r - i, p[mirror])
    while t[i + p[i] + 1] == t[i - p[i] - 1]:
        p[i] += 1
    if i + p[i] > r:
        c, r = i, i + p[i]
for i in range(1, n - 1):
    if t[i] != "#":
        print(f"  中心 {t[i]!r}（位置 {i}）：半径 {p[i]}")

# ---- 复杂度 ----
print("\n== 复杂度 ==")
print("  暴力枚举中心：O(n²)")
print("  Manacher：O(n)（每个位置最多扩展一次）")
print("  空间：O(n) 存转换串与 p 数组")

# ---- 注意事项 ----
print("\n== 注意事项 ==")
for item in [
    "分隔符必须是原串中不存在的字符（或用哨兵 ^ $）",
    "多个等长回文时，本实现返回第一个最长的",
    "p[i] 是转换串中的半径，原串长度 = p[i]",
    "求“回文子序列”（不连续）要用区间 DP（第494课）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 返回所有最长回文子串的位置。
# 2. 用 Manacher 判断一个字符串能否通过删除最多一个字符变成回文。
# 3. 统计字符串中回文子串的总数（提示：sum((p[i]+1)//2)）。
# 4. 思考：为什么插入分隔符后所有回文都变成奇数长度？
