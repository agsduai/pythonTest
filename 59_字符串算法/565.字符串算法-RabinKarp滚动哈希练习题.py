# ===== 第565课：字符串算法-Rabin-Karp滚动哈希 =====
# 知识点：
#   - 把字符串映射成数字（哈希），用“滚动”方式 O(1) 更新窗口哈希
#   - 窗口右移：hash = (hash - 左字符×base^(m-1)) × base + 新字符
#   - 哈希相等后再逐字符验证，防止碰撞误报
#   - 期望 O(n+m)；最坏（大量碰撞）退化为 O(nm)
#   - 优势：易扩展到多模式匹配、二维匹配、最长重复子串
#   - 与 Python 内置 hash 的区别：需要“可滚动、固定模数”，不能用随机化哈希
# 依赖：无


def rabin_karp(text: str, pattern: str, base: int = 256,
               mod: int = 1_000_000_007) -> tuple[list[int], int]:
    """返回 (匹配起点, 哈希命中次数)。"""
    n, m = len(text), len(pattern)
    if m == 0 or m > n:
        return [], 0

    high = pow(base, m - 1, mod)          # base^(m-1)
    pattern_hash = 0
    window_hash = 0
    for ch in pattern:
        pattern_hash = (pattern_hash * base + ord(ch)) % mod
    for ch in text[:m]:
        window_hash = (window_hash * base + ord(ch)) % mod

    matches = []
    hash_hits = 0
    for start in range(n - m + 1):
        if window_hash == pattern_hash:
            hash_hits += 1
            if text[start:start + m] == pattern:   # 验证，防碰撞
                matches.append(start)
        if start < n - m:
            # 去掉左字符、加上右字符
            window_hash = (
                (window_hash - ord(text[start]) * high) * base
                + ord(text[start + m])
            ) % mod
    return matches, hash_hits


print("== 基本匹配 ==")
text = "ababcababcabc"
pattern = "abc"
matches, hits = rabin_karp(text, pattern)
print(f"  主串：{text}")
print(f"  模式：{pattern}")
print(f"  匹配起点：{matches}")
print(f"  哈希命中次数：{hits}（含碰撞验证）")

# ---- 滚动哈希逐步演示 ----
print("\n== 滚动过程（窗口长度 3）==")
base, mod = 256, 1_000_000_007
m = 3
h = 0
for ch in text[:m]:
    h = (h * base + ord(ch)) % mod
print(f"  初始窗口 {text[:m]!r}: hash={h}")
for start in range(1, len(text) - m + 1):
    h = ((h - ord(text[start - 1]) * pow(base, m - 1, mod)) * base
         + ord(text[start + m - 1])) % mod
    if start < 8:
        print(f"  窗口 {text[start:start + m]!r}: hash={h}")

# ---- 多模式匹配 ----
print("\n== 多模式：分别跑 Rabin-Karp ==")
text2 = "the quick brown fox jumps over the lazy dog"
for p in ("the", "fox", "dog"):
    pos, _ = rabin_karp(text2, p)
    print(f"  {p!r} → {pos}")

# ---- 碰撞演示 ----
print("\n== 碰撞与验证 ==")
# 人为把 mod 调得很小，制造大量哈希碰撞
text3 = "abcabdabeabf"
pattern3 = "abc"
matches3, hits3 = rabin_karp(text3, pattern3, base=256, mod=7)
print(f"  mod=7 时哈希命中 {hits3} 次，实际匹配 {matches3}")
print("  命中多但验证后只保留真实匹配 —— 验证步骤不可省")

# ---- 复杂度与选择 ----
print("\n== 复杂度 ==")
print("  预处理模式哈希：O(m)")
print("  滚动扫描：O(n)")
print("  每次哈希命中验证：O(m)，期望碰撞很少")
print("  期望 O(n+m)，最坏 O(nm)")

print("\n== 适用场景 ==")
for item in [
    "多模式/二维匹配（每行滚动哈希）",
    "最长重复子串（二分长度 + 哈希去重）",
    "抄袭检测/相似片段查找",
    "不适合安全敏感场景（哈希可被构造碰撞）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 修改 base 与 mod，观察匹配结果是否仍正确。
# 2. 实现“只返回第一个匹配”的版本。
# 3. 用滚动哈希求字符串的最长重复子串（二分长度）。
# 4. 思考：为什么哈希命中后必须逐字符验证？
