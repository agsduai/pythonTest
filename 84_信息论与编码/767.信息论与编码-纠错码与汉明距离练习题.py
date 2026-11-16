# ===== 第767课：信息论与编码-纠错码与汉明距离 =====
# 知识点：
#   - 汉明距离 d(x,y)：两等长码字不同位的个数；最小距离 d_min 决定纠错能力
#   - 检错 e 位需 d_min >= e+1；纠错 t 位需 d_min >= 2t+1
#   - 汉明(7,4)：4 数据位 + 3 校验位，d_min=3，可纠 1 位错、检 2 位错
#   - 奇偶校验矩阵 H：伴随式 syndrome = H·r 直接指出错误位置
#   - 码率 R = k/n；纠错能力与码率互相权衡（第765课香农限）
#   - 与 CRC（检错不纠错）、R S 码（纠突发错）对比
# 依赖：无（标准库）
import itertools
import random


def hamming_distance(a, b):
    return sum(x != y for x, y in zip(a, b))


def min_distance(codewords):
    return min(hamming_distance(a, b)
               for i, a in enumerate(codewords) for b in codewords[i+1:])


# ---- Hamming(7,4)：位置 1,2,4 为校验位（1-indexed）----
DATA_POS = [3, 5, 6, 7]
CHECK_POS = [1, 2, 4]


def hamming74_encode(nibble):
    """4 位数据 -> 7 位码字（列表，1-indexed 用 0 占位）。"""
    d = [(nibble >> i) & 1 for i in range(3, -1, -1)]   # d3,d2,d1,d0
    c = [0]*8
    for pos, bit in zip(DATA_POS, d):
        c[pos] = bit
    # 校验位：覆盖所有「该位置二进制位为 1」的位置
    for p in CHECK_POS:
        c[p] = sum(c[j] for j in range(1, 8) if j != p and (j & p)) % 2
    return tuple(c[1:])


def hamming74_decode(codeword):
    """返回 (纠正后的 4 位数据, 错误位置 0=无错/纠正, 是否可纠)。"""
    c = [0] + list(codeword)
    syndrome = 0
    for p in CHECK_POS:
        parity = sum(c[j] for j in range(1, 8) if (j & p)) % 2
        if parity:
            syndrome |= p
    if syndrome:
        if 1 <= syndrome <= 7:
            c[syndrome] ^= 1
        else:
            return None, syndrome, False
    data = 0
    for pos in DATA_POS:
        data = (data << 1) | c[pos]
    return data, syndrome, True


print("== 汉明距离与最小距离 ==")
for a, b in (("1010101","1000101"), ("0000000","1111111"), ("abc","abd")):
    print(f"  d({a},{b}) = {hamming_distance(a,b)}")

CW = [hamming74_encode(n) for n in range(16)]
print(f"\n== Hamming(7,4) 码本 ==")
for n, cw in enumerate(CW[:6]):
    print(f"  数据 {n:04b} -> 码字 {''.join(map(str,cw))}")
print(f"  码字数={len(CW)} 最小距离 d_min={min_distance(CW)}")
print("  d_min=3 -> 可纠 1 位错 (t=1)、检 2 位错 (e=2)")

print("\n== 无错译码 ==")
for n in (0, 5, 9, 15):
    val, syn, ok = hamming74_decode(CW[n])
    print(f"  {n:>2} -> 译码 {val:>2} syndrome={syn} 一致={val==n}")

print("\n== 纠 1 位错 ==")
r = random.Random(3)
for n in (3, 7, 12):
    cw = list(CW[n])
    pos = r.randrange(7)
    cw[pos] ^= 1
    val, syn, ok = hamming74_decode(tuple(cw))
    print(f"  数据 {n:>2}, 第 {pos+1} 位翻转 -> syndrome={syn}(指出位置) "
          f"译码={val} 纠正成功={val==n and ok}")

print("\n== 2 位错：能检测但会误纠 ==")
cw = list(CW[6]); cw[0] ^= 1; cw[3] ^= 1
val, syn, ok = hamming74_decode(tuple(cw))
print(f"  原数据 6，翻转 2 位 -> syndrome={syn}, 译码={val}（错误，说明只能纠 1 位）")
print("  SECDED：再加一个全局奇偶位，可纠 1 位 + 检 2 位")

print("\n== 随机误码率实测（BSC p=0.05）==")
def simulate(p, trials=5000, seed=1):
    rng = random.Random(seed)
    errors = 0
    for _ in range(trials):
        n = rng.randrange(16)
        cw = list(CW[n])
        for i in range(7):
            if rng.random() < p:
                cw[i] ^= 1
        val, _, _ = hamming74_decode(tuple(cw))
        if val != n:
            errors += 1
    return errors / trials

for p in (0.01, 0.02, 0.05, 0.1):
    raw = p                                 # 未编码时数据位出错概率近似
    coded = simulate(p, trials=3000)
    # 理论：7 位里 >=2 位错才译错
    theo = 1 - (1-p)**7 - 7*p*(1-p)**6
    print(f"  p={p:.2f}: 未编码≈{raw:.3f} 汉明码实测={coded:.4f} "
          f"理论(≥2位错)={theo:.4f}")
print("  低误码率下改善明显；p 变大后纠正能力饱和")

print("\n== 检错码：CRC 与奇偶位 ==")
def parity_bit(bits): return sum(bits) % 2
def crc8(data, poly=0x07):
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ poly) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc
msg = b"hello world"
print(f"  奇偶位: {''.join(map(str,[1,0,1,1]))} -> {parity_bit([1,0,1,1])}")
print(f"  CRC8({msg!r}) = 0x{crc8(msg):02X}")
corrupt = bytearray(msg); corrupt[3] ^= 0x20
print(f"  改 1 字节后 CRC = 0x{crc8(bytes(corrupt)):02X}（不同 -> 检出）")
print("  CRC 只能检错，不定位/不纠正；常与重传(ARQ)配合")

print("\n== 编码权衡 ==")
print(f"  {'码':<14}{'码率 R':<10}{'d_min':<8}{'能力'}")
for row in (("重复码(3)", "1/3", "3", "纠1位"),
            ("Hamming(7,4)", "4/7≈0.57", "3", "纠1位"),
            ("Hamming(15,11)", "11/15≈0.73", "3", "纠1位"),
            ("RS(255,223)", "≈0.87", "33", "纠16符号错")):
    print(f"  {row[0]:<14}{row[1]:<10}{row[2]:<8}{row[3]}")

print("\n== 应用 ==")
for line in [
    "  内存 ECC、磁盘/SSD、二维码（RS 码）、深空通信（LDPC/Turbo）",
    "  与第765课信道容量呼应：好码在 R<C 下把误码压到任意小",
    "  与第705课 Merkle/第601课 CRC 同属「完整性」工具箱",
    "  生产用 reedsolo / zfec 等库，本课是原理版",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 SECDED(8,4)：加全局奇偶位，区分 1 位错与 2 位错。
# 2. 实现 CRC32（IEEE 多项式）并与 zlib.crc32 对照。
# 3. 用生成矩阵 G 与校验矩阵 H 重写 Hamming(7,4) 编解码。
# 4. 思考：为什么 d_min=2t+1 才能纠 t 位错（球装填直觉）？
