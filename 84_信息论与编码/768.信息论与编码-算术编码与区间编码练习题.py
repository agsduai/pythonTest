# ===== 第768课：信息论与编码-算术编码与区间编码 =====
# 知识点：
#   - 算术编码：把整条消息映射到 [0,1) 的一个子区间，输出区间内任意一个小数
#   - 每个符号按概率把当前区间 [low, high) 按比例切分，选对应子区间继续
#   - 平均码长可突破哈夫曼的 H+1，非常接近熵；尤其适合偏斜分布
#   - 与哈夫曼区别：不逐符号赋码字，整条消息一个码；可非整数 bit/符号
#   - 有限精度实现要处理「区间缩放/重归一化」，本课用 Python 任意精度整数演示
#   - 解码：同一个概率模型，按小数落在哪个子区间逐步还原符号
# 依赖：无（标准库）
import math
from collections import Counter
from fractions import Fraction


def build_model(text):
    n = len(text)
    counts = Counter(text)
    # 累积区间（用 Fraction 避免浮点误差）
    cum, acc = {}, Fraction(0, 1)
    for s in sorted(counts):
        cum[s] = (acc, acc + Fraction(counts[s], n))
        acc += Fraction(counts[s], n)
    return cum


def arithmetic_encode(text, cum):
    low, high = Fraction(0, 1), Fraction(1, 1)
    for ch in text:
        a, b = cum[ch]
        width = high - low
        high = low + width * b
        low = low + width * a
    return (low + high) / 2          # 区间内任取一点


def arithmetic_decode(value, cum, length):
    out = []
    low, high = Fraction(0, 1), Fraction(1, 1)
    for _ in range(length):
        width = high - low
        target = (value - low) / width
        for s, (a, b) in cum.items():
            if a <= target < b:
                out.append(s)
                high = low + width * b
                low = low + width * a
                break
        else:
            raise ValueError("码值不在任何符号区间")
    return "".join(out)


print("== 概率模型（累积区间）==")
text = "ABRACADABRA"
cum = build_model(text)
for s in sorted(cum):
    a, b = cum[s]
    print(f"  {s}: [{float(a):.4f}, {float(b):.4f}) 宽={float(b-a):.4f}")

print("\n== 编码：区间逐步收窄 ==")
low, high = Fraction(0,1), Fraction(1,1)
for i, ch in enumerate(text[:6]):
    a,b = cum[ch]; w = high-low
    high, low = low + w*b, low + w*a
    print(f"  +{ch} -> [{float(low):.6f}, {float(high):.6f}) 宽={float(high-low):.8f}")
value = arithmetic_encode(text, cum)
print(f"  最终编码值 ≈ {float(value):.12f}（Fraction={value}）")
print(f"  理论码长 ≈ -log2(区间宽) bit")

print("\n== 解码往返 ==")
back = arithmetic_decode(value, cum, len(text))
print(f"  解码结果 = {back!r}  与原文一致={back == text}")

print("\n== 与哈夫曼/定长码的码长对比 ==")
freq = Counter(text)
def entropy_of(freq):
    n = sum(freq.values())
    return -sum((w/n)*math.log2(w/n) for w in freq.values())
H = entropy_of(freq)
n = len(text)
# 区间宽度 = 各符号概率之积
width = Fraction(1,1)
for ch in text:
    width *= (cum[ch][1]-cum[ch][0])
ideal_bits = -math.log2(float(width))
huff_bits_lower = n * H
fixed_bits = n * math.ceil(math.log2(len(freq)))
print(f"  消息长度 {n} 符号, 熵 H={H:.4f} bit/符号")
print(f"  熵下界 n·H     = {huff_bits_lower:.2f} bit")
print(f"  算术编码理论   ≈ {ideal_bits:.2f} bit（≈ -log2 区间宽）")
print(f"  哈夫曼上界     < {n*(H+1):.2f} bit")
print(f"  定长码         = {fixed_bits} bit")
print("  算术编码可突破 H+1，但需要足够长的消息摊薄模型/终止开销")

print("\n== 偏斜分布下的优势 ==")
for name, t in (("均匀", "ABCD"*25), ("偏斜", "A"*97+"B"*2+"C"),
                ("极端偏斜", "A"*999+"B")):
    c = build_model(t)
    v = arithmetic_encode(t, c)
    ok = arithmetic_decode(v, c, len(t)) == t
    w = Fraction(1,1)
    for ch in t: w *= (c[ch][1]-c[ch][0])
    bits = -math.log2(float(w)) if float(w) > 0 else float("inf")
    ent = entropy_of(Counter(t))
    print(f"  {name:<10}: 长度={len(t):>4} 理论码长≈{bits:>8.1f} bit "
          f"({bits/len(t):.3f} bit/符号) 熵={ent:.3f} 往返={ok}")

print("\n== 有限精度与重归一化（工程要点）==")
for line in (
    "  真实实现用 32/64 位整数维护 low/high，区间太窄时「放大」并输出高位",
    "  常见策略：E1/E2/E3 缩放（区间全在上半/下半/跨中点）",
    "  解码器必须做完全相同的缩放，否则漂移",
    "  结束时要输出足够的位让区间唯一可辨，并加终止符或长度头",
):
    print(" ", line)

print("\n== 编码方法谱系 ==")
print(f"  {'方法':<14}{'粒度':<14}{'接近熵':<10}{'典型'}")
for row in (("哈夫曼", "整数 bit/符号", "H~H+1", "ZIP/PNG"),
            ("算术编码", "整条消息", "极接近 H", "JPEG2000/H.264 CABAC"),
            ("区间编码", "整条消息", "极接近 H", "lzma/rANS 前身"),
            ("ANS/FSE", "符号但非整数", "极接近 H", "zstd/现代压缩器")):
    print(f"  {row[0]:<14}{row[1]:<14}{row[2]:<10}{row[3]}")

print("\n== 应用 ==")
for line in [
    "  JPEG2000、H.264/H.265 CABAC、PDF、LZMA 的高阶熵编码",
    "  自适应模型（PPM/上下文混合）配合算术编码可压到极低熵",
    "  与第764课哈夫曼、第766课 LZ77 组合成完整压缩器",
    "  加密/压缩顺序：先压缩去冗余再加密，否则密文不可压",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现整数版算术编码（32 位 low/high + E1/E2/E3 缩放）。
# 2. 给编码加自适应概率模型，边编码边更新频率。
# 3. 对比算术编码与哈夫曼在「极端偏斜」分布下的实际输出位数。
# 4. 思考：为什么算术编码能突破哈夫曼的 H+1 上界？
