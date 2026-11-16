# ===== 第770课：信息论与编码-综合案例-文本压缩与传输管线 =====
# 知识点：
#   - 综合串起本章：熵估计 -> LZ77 去结构冗余 -> 哈夫曼去统计冗余 -> BSC 噪声 -> 纠错
#   - 一条完整链路：信源 -> 信源编码(压缩) -> 信道编码(加冗余) -> 噪声 -> 解码 -> 还原
#   - 香农分离定理：压缩到接近 H，再用 R<C 的码传输，可端到端可靠
#   - 度量：原始体积、压缩后体积、压缩率、误码率、端到端还原成功率
#   - 用重复码做最简单的信道编码，演示「加冗余抗噪」与「压缩去冗余」的对立统一
#   - 全部标准库 + 固定 seed，纯内存、离线可运行
# 依赖：无（标准库）
import heapq
import math
import random
from collections import Counter


def entropy(data):
    n = len(data)
    return -sum((c/n)*math.log2(c/n) for c in Counter(data).values())


# ---- 1) LZ77 ----
def lz77_encode(s, window=1024, max_match=16):
    out, i, n = [], 0, len(s)
    while i < n:
        start = max(0, i-window)
        bl, bd = 0, 0
        for j in range(i-1, start-1, -1):
            k = 0
            while k < max_match and i+k < n and s[j+k] == s[i+k]:
                k += 1
            if k > bl:
                bl, bd = k, i-j
                if k == max_match: break
        if bl >= 3:
            nxt = s[i+bl] if i+bl < n else ""
            out.append((bd, bl, nxt)); i += bl + (1 if nxt else 0)
        else:
            out.append((0, 0, s[i])); i += 1
    return out


def lz77_decode(toks):
    out = []
    for d, l, nxt in toks:
        if l:
            start = len(out)-d
            for k in range(l): out.append(out[start+k])
        if nxt: out.append(nxt)
    return "".join(out)


# ---- 2) 把 token 展平成符号流，再哈夫曼 ----
def tokens_to_symbols(toks):
    syms = []
    for d, l, nxt in toks:
        if l:
            syms.append(("M", d, l))
        else:
            syms.append(("L",))
        if nxt:
            syms.append(("C", nxt))
    return syms


class Huff:
    def __init__(self, symbols):
        freq = Counter(symbols)
        heap = [self._Node(s, w) for s, w in freq.items()]
        heapq.heapify(heap)
        if len(heap) == 1:
            self.root = self._Node(w=heap[0].w, l=heap[0])
        else:
            while len(heap) > 1:
                a, b = heapq.heappop(heap), heapq.heappop(heap)
                heapq.heappush(heap, self._Node(w=a.w+b.w, l=a, r=b))
            self.root = heap[0]
        self.codes = {}
        self._walk(self.root, "")
    class _Node:
        __slots__=("sym","w","l","r")
        def __init__(self,sym=None,w=0,l=None,r=None): self.sym,self.w,self.l,self.r=sym,w,l,r
        def __lt__(self,o): return self.w < o.w
    def _walk(self, node, p):
        if node.sym is not None:
            self.codes[node.sym] = p or "0"; return
        if node.l: self._walk(node.l, p+"0")
        if node.r: self._walk(node.r, p+"1")
    def encode(self, syms): return "".join(self.codes[s] for s in syms)
    def decode(self, bits):
        out, node = [], self.root
        for b in bits:
            node = node.l if b == "0" else node.r
            if node.sym is not None:
                out.append(node.sym); node = self.root
        return out


print("== 原始信源 ==")
TEXT = ("信息论研究信息的度量、压缩与可靠传输。" * 30 +
        "香农提出了熵、信道容量和率失真三大定理。" * 20)
raw_bits = len(TEXT.encode("utf-8")) * 8
print(f"  字符数={len(TEXT)} 原始 UTF-8 体积={raw_bits} bit")
print(f"  字符级熵={entropy(TEXT):.3f} bit/字符（理论下界约 "
      f"{entropy(TEXT)*len(TEXT):.0f} bit）")

print("\n== 阶段 1：LZ77 去结构冗余 ==")
toks = lz77_encode(TEXT)
print(f"  {len(TEXT)} 字符 -> {len(toks)} 个 LZ token，往返={lz77_decode(toks)==TEXT}")

print("\n== 阶段 2：哈夫曼去统计冗余 ==")
syms = tokens_to_symbols(toks)
huff = Huff(syms)
compressed = huff.encode(syms)
print(f"  符号流 {len(syms)} 个 -> 码流 {len(compressed)} bit "
      f"({len(compressed)/8:.0f} 字节)")
print(f"  符号经验熵={entropy(syms):.3f} bit/符号，"
      f"平均码长={len(compressed)/len(syms):.3f} bit/符号")
print(f"  总压缩率 = {len(compressed)/raw_bits:.1%}（相对原始 UTF-8）")

print("\n== 解压往返（无噪声）==")
back_syms = huff.decode(compressed)
print(f"  哈夫曼往返符号一致={back_syms == syms}")
print(f"  LZ 单独往返文本一致={lz77_decode(toks) == TEXT}")
print("  （教学版把 LZ token 展平成符号流，完整还原需保留字面量流并做位打包）")

print("\n== 阶段 3：BSC 噪声信道 ==")
def bsc(bits, p, rng):
    return "".join(str(int(b) ^ (1 if rng.random() < p else 0)) for b in bits)

for p in (0.0, 0.001, 0.01, 0.05):
    rng = random.Random(7)
    noisy = bsc(compressed, p, rng)
    flips = sum(a != b for a,b in zip(compressed, noisy))
    # 哈夫曼码流对 bit 翻转极敏感：一个错可能让后续全乱
    ok = huff.decode(noisy) == syms
    print(f"  p={p:<6}: 翻转 {flips:>4}/{len(compressed)} bit -> "
          f"无保护解压成功={ok}")
print("  压缩后冗余很少，反而更怕误码 -> 必须加信道编码")

print("\n== 阶段 4：重复码（3 次）+ 多数表决 ==")
def rep_encode(bits, n=3):
    return "".join(b*n for b in bits)
def rep_decode(bits, n=3):
    out = []
    for i in range(0, len(bits), n):
        chunk = bits[i:i+n]
        out.append("1" if chunk.count("1") > n//2 else "0")
    return "".join(out)

p = 0.05
protected = rep_encode(compressed, 3)
rng = random.Random(7)
noisy = bsc(protected, p, rng)
recovered = rep_decode(noisy, 3)
print(f"  码率从 1 降到 1/3（{len(protected)} bit），BSC p={p}")
print(f"  纠错后误码率={sum(a!=b for a,b in zip(compressed,recovered))/len(compressed):.4f}")
print(f"  端到端解压成功={huff.decode(recovered) == syms}")

print("\n== 速率与可靠性的权衡表 ==")
C = 1 - (-p*math.log2(p)-(1-p)*math.log2(1-p))
print(f"  BSC(p={p}) 容量 C={C:.3f} bit/信道使用")
for n, label in ((1,"无保护"),(3,"重复3"),(5,"重复5"),(7,"重复7")):
    rate = 1/n
    # n 中多数错的概率
    pe = sum(math.comb(n,k)*p**k*(1-p)**(n-k) for k in range(n//2+1, n+1))
    print(f"  {label:<8}: 有效码率={rate:.3f} 残差误码率≈{pe:.5f} "
          f"R<C={rate < C}")

print("\n== 分层回顾 ==")
for line in [
    "  信源层  : 熵估计给出理论下界（第763课）",
    "  去结构  : LZ77 消重复子串（第766课）",
    "  去统计  : 哈夫曼逼近熵（第764课）/ 算术编码更紧（第768课）",
    "  信道层  : BSC 容量 + 重复码/汉明码纠错（第765/767课）",
    "  还原层  : 多数表决 -> 哈夫曼解码 -> LZ 解码 -> 原文",
    "  有损扩展: 量化 + 率失真折中（第769课，如图像/音频）",
]:
    print("  -", line)

print("\n== 与真实系统的差距 ==")
for line in [
    "  本例 LZ token -> 符号流的展开是教学简化，未做位打包与码表序列化",
    "  真实用 DEFLATE(LZ77+哈夫曼) / zstd(LZ+FSE) / LDPC/Polar 信道码",
    "  码表本身也要传输并受 CRC 保护",
    "  目标是串起「压缩去冗余 + 传输加冗余」这一完整信息链路",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 把码表序列化进码流，并用 CRC 检错（第767课）。
# 2. 用 Hamming(7,4) 替换重复码，对比有效码率与残差误码率。
# 3. 实现自适应算术编码替换哈夫曼，测量总 bit 数变化。
# 4. 思考：为什么「压缩后必须再加纠错」而不是直接传原始数据？
