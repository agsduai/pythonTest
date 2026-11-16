# ===== 第607课：国际化与本地化-Unicode与正规化 =====
# 知识点：
#   - 同一个「视觉字符」可能有多种码位序列：é = U+00E9 或 e + U+0301
#   - NFC 合成 / NFD 分解；NFKC / NFKD 还会做「兼容」转换（全角、上标、连字）
#   - 比较、去重、做主键前必须先 normalize，否则看似相同的字符串不相等
#   - combining(char) 判断组合记号；用 NFD + 过滤可去除重音
#   - casefold() 比 lower() 更适合无大小写比较（ß -> ss）
#   - east_asian_width：W/F 为全角，用于终端对齐；name/category 做字符分类
#   - 同形异义字（confusable）是安全风险，正规化不能解决，需专门表
# 依赖：无（标准库）
import unicodedata

a = "é"                 # U+00E9 预组合
b = "e\u0301"           # e + COMBINING ACUTE ACCENT
print("== 看起来一样，其实不同 ==")
print(f"  a = {a!r}  码位 {[hex(ord(c)) for c in a]}")
print(f"  b = {b!r}  码位 {[hex(ord(c)) for c in b]}")
print("  直接相等:", a == b, "| NFC 后相等:", unicodedata.normalize("NFC", b) == a)

print("\n== 四种正规化形式 ==")
samples = ["Café", "ﬁ", "ＡＢＣ", "①", "²", "㍿"]
for s in samples:
    forms = {f: unicodedata.normalize(f, s) for f in ("NFC", "NFD", "NFKC", "NFKD")}
    print(f"  {s!r:<10} NFC={forms['NFC']!r:<12} NFD={forms['NFD']!r:<14} "
          f"NFKC={forms['NFKC']!r:<12} NFKD={forms['NFKD']!r}")

print("\n== 用正规化做去重 ==")
words = ["Café", "Cafe\u0301", "Ｃａｆｅ", "CAFÉ"]
seen = {}
for w in words:
    key = unicodedata.normalize("NFKC", w).casefold()
    seen.setdefault(key, []).append(w)
print("  分组结果:", seen)
print(f"  {len(words)} 个写法 -> {len(seen)} 个规范键")

print("\n== 去除重音（NFD + 过滤组合记号）==")
def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c))

for s in ("Café", " naïve ", "São Paulo", "Žluťoučký"):
    print(f"  {s!r:<16} -> {strip_accents(s)!r}")

print("\n== casefold 与 lower 的区别 ==")
for s in ("Straße", "İ", "ΣΙΣΥΦΟΣ"):
    print(f"  {s!r:<12} lower={s.lower()!r:<16} casefold={s.casefold()!r}")
print("  'Straße'.casefold() == 'strasse':", "Straße".casefold() == "strasse")

print("\n== 字符属性 ==")
for ch in "A中１！😀\u0301":
    print(f"  {ch!r:<8} name={unicodedata.name(ch, '?')[:28]:<30} "
          f"cat={unicodedata.category(ch)} width={unicodedata.east_asian_width(ch)} "
          f"combining={unicodedata.combining(ch)}")

print("\n== 终端显示宽度（全角算 2）==")
def display_width(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)

for s in ("abc", "中文", "ＡＢＣ", "中a文"):
    print(f"  {s!r:<10} 宽度={display_width(s)}")
print("  对齐示例:", "中文".ljust(8 - (display_width("中文") - len("中文"))) + "|")

print("\n== 同形异义字（正规化无法解决）==")
latin_a, cyrillic_a = "a", "\u0430"
print(f"  拉丁 a 与西里尔 а 看起来像，NFC 后相等吗: "
      f"{unicodedata.normalize('NFC', latin_a) == unicodedata.normalize('NFC', cyrillic_a)}")
print("  用户标识/域名需 confusable 检测或白名单，不能只靠 normalize")

print("\n== 编码与码位 ==")
s = "你好😀"
print(f"  {s!r}: 字符数={len(s)} UTF-8 字节数={len(s.encode('utf-8'))}")
print("  码位:", [f"U+{ord(c):04X}" for c in s])

# ===== 练习题 =====
# 1. 写 canonical_key(s)：NFKC + casefold + 去首尾空白，用于用户昵称去重。
# 2. 统计一段多语言文本里各 Unicode category 的字符数。
# 3. 实现按显示宽度截断字符串的函数，保证不会截出半个字符。
# 4. 思考：为什么 NFKC 适合做搜索索引，却不适合作为密码的规范化形式？
