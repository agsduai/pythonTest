# ===== 第563课：字符串算法-暴力匹配与问题定义 =====
# 知识点：
#   - 字符串匹配：在主串 text 中找模式串 pattern 的所有出现位置
#   - 暴力法：每个起点都逐字符比较，最坏 O(n×m)
#   - 最坏例子：text = "aaaa...aab"，pattern = "aaaa...b"（大量重复前缀）
#   - 暴力法优点：实现简单、无预处理、短模式串足够用
#   - 后续优化方向：KMP（利用已匹配信息）、Rabin-Karp（哈希）、Z（前缀函数）
#   - 与第15章正则的区别：这里手写精确匹配算法，理解底层
# 依赖：无


def brute_force_search(text: str, pattern: str) -> tuple[list[int], int]:
    """返回 (所有匹配起点, 字符比较次数)。"""
    if not pattern:
        return [], 0
    n, m = len(text), len(pattern)
    matches = []
    comparisons = 0
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


print("== 基本示例 ==")
text = "ababcababcabc"
pattern = "abc"
matches, comparisons = brute_force_search(text, pattern)
print(f"  主串：{text}")
print(f"  模式：{pattern}")
print(f"  匹配起点：{matches}")
print(f"  比较次数：{comparisons}")
print(f"  与 str.find 对照：{[i for i in range(len(text)) if text.startswith(pattern, i)]}")

# ---- 最坏情况 ----
print("\n== 最坏情况：大量重复前缀 ==")
n = 30
text_bad = "a" * n + "b"
pattern_bad = "a" * (n - 1) + "b"
matches_bad, comp_bad = brute_force_search(text_bad, pattern_bad)
print(f"  主串长度 {len(text_bad)}，模式长度 {len(pattern_bad)}")
print(f"  匹配起点：{matches_bad}")
print(f"  比较次数：{comp_bad}（约 n×m = {len(text_bad) * len(pattern_bad)}）")
print("  每个起点都要比较到最后一个字符才发现不匹配")

# ---- 平均情况 ----
print("\n== 平均情况 ==")
import random
random.seed(7)
random_text = "".join(random.choice("abcd") for _ in range(200))
random_pattern = "abc"
m, c = brute_force_search(random_text, random_pattern)
print(f"  随机文本 200 字符，模式 {random_pattern!r}")
print(f"  匹配 {len(m)} 次，比较 {c} 次（接近线性，因为很快失配）")

# ---- 多模式匹配 ----
print("\n== 多模式匹配：多次调用暴力法 ==")
patterns = ["abc", "bca", "cab"]
text2 = "abcabcabc"
for p in patterns:
    pos, _ = brute_force_search(text2, p)
    print(f"  {p!r} → {pos}")
print("  多模式时复杂度会乘以模式数量 → 需要 Aho-Corasick（第568课）")

# ---- 复杂度对照 ----
print("\n== 算法对照 ==")
rows = [
    ("暴力", "O((n-m+1)×m)", "实现最简单", "重复前缀极慢"),
    ("KMP", "O(n+m)", "稳定线性", "需要前缀表、理解成本"),
    ("Rabin-Karp", "O(n+m) 期望", "易扩展多模式", "哈希冲突、取模"),
    ("Z 算法", "O(n+m)", "代码短", "拼接串占额外空间"),
]
print(f"  {'算法':<12}{'复杂度':<18}{'优点':<18}{'缺点'}")
for r in rows:
    print(f"  {r[0]:<12}{r[1]:<18}{r[2]:<18}{r[3]}")

# ===== 练习题 =====
# 1. 统计暴力法在随机文本上的比较次数与 n 的关系。
# 2. 实现“只找第一个匹配”的暴力版本，提前返回。
# 3. 构造一个暴力法特别慢的输入（提示：重复字符 + 末尾不同）。
# 4. 思考：为什么 Python 内置的 str.find 通常比手写暴力快？
