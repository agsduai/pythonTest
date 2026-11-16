# ===== 第764课：信息论与编码-哈夫曼编码与前缀码 =====
# 知识点：
#   - 前缀码 prefix code：任一码字都不是另一码字的前缀，可无歧义即时解码
#   - 哈夫曼编码：按频率建最优二叉树，高频短码、低频长码，平均码长接近熵
#   - 算法：优先堆反复合并两个最小权重节点，直到剩一棵树
#   - 平均码长 L = Σ p_i·l_i，满足 H <= L < H+1（bit/符号）
#   - 与定长编码对比：定长 ceil(log2 n) bit，哈夫曼在偏斜分布下显著更省
#   - 解码：从根沿比特走，到叶子输出符号并回到根
#   - 应用：ZIP/PNG/JPEG/MP3 的熵编码阶段、压缩传输
# 依赖：无（标准库）
import heapq
import math
from collections import Counter


class HuffNode:
    __slots__ = ("symbol", "weight", "left", "right")
    def __init__(self, symbol=None, weight=0, left=None, right=None):
        self.symbol, self.weight = symbol, weight
        self.left, self.right = left, right
    def __lt__(self, other):
        return self.weight < other.weight


def build_tree(freq):
    heap = [HuffNode(s, w) for s, w in freq.items()]
    heapq.heapify(heap)
    if len(heap) == 1:                      # 只有一种符号的退化情况
        return HuffNode(left=heap[0], weight=heap[0].weight)
    while len(heap) > 1:
        a, b = heapq.heappop(heap), heapq.heappop(heap)
        heapq.heappush(heap, HuffNode(weight=a.weight+b.weight, left=a, right=b))
    return heap[0]


def build_codes(root):
    codes = {}
    def walk(node, prefix):
        if node.symbol is not None:
            codes[node.symbol] = prefix or "0"
            return
        if node.left: walk(node.left, prefix+"0")
        if node.right: walk(node.right, prefix+"1")
    walk(root, "")
    return codes


def encode(text, codes):
    return "".join(codes[ch] for ch in text)


def decode(bits, root):
    out, node = [], root
    for b in bits:
        node = node.left if b == "0" else node.right
        if node.symbol is not None:
            out.append(node.symbol); node = root
    return "".join(out)


def entropy(freq):
    n = sum(freq.values())
    return -sum((w/n)*math.log2(w/n) for w in freq.values() if w > 0)


def avg_len(freq, codes):
    n = sum(freq.values())
    return sum(freq[s]*len(codes[s]) for s in freq) / n


print("== 构造哈夫曼码 ==")
freq = Counter("this is an example of a huffman tree")
print("  频率:", dict(sorted(freq.items())))
root = build_tree(freq)
codes = build_codes(root)
for s in sorted(codes, key=lambda x: (len(codes[x]), x)):
    print(f"    {s!r:<6} freq={freq[s]:<3} code={codes[s]:<8} len={len(codes[s])}")

print("\n== 前缀码校验 ==")
def is_prefix_free(cs):
    values = list(cs.values())
    return all(not v.startswith(u) for i,u in enumerate(values)
               for j,v in enumerate(values) if i != j)
print("  无码字是另一码字前缀:", is_prefix_free(codes))

print("\n== 编码 / 解码往返 ==")
text = "this is an example of a huffman tree"
bits = encode(text, codes)
back = decode(bits, root)
print(f"  原文长度={len(text)*8} bit(定长8bit/char)  哈夫曼={len(bits)} bit")
print(f"  往返一致: {back == text}")
print(f"  码流前 48 位: {bits[:48]}...")

print("\n== 熵、平均码长、定长码对比 ==")
H, L = entropy(freq), avg_len(freq, codes)
fixed = math.ceil(math.log2(len(freq)))
print(f"  熵 H(X)       = {H:.4f} bit/符号（理论下界）")
print(f"  哈夫曼平均码长 = {L:.4f} bit/符号")
print(f"  等长码         = {fixed} bit/符号")
print(f"  满足 H <= L < H+1: {H <= L < H+1}")
print(f"  相对等长码节省 = {1-L/fixed:.1%}，压缩率 = {L/8:.1%}（相对 8bit ASCII）")

print("\n== 分布越偏斜，收益越大 ==")
for name, data in (("均匀 8 符号", "abcdefgh"*32),
                   ("轻度偏斜", "aaaaaaabc"*20),
                   ("高度偏斜", "a"*500 + "b"*10 + "c"*2)):
    f = Counter(data)
    r = build_tree(f); c = build_codes(r)
    h, l = entropy(f), avg_len(f, c)
    fixed = math.ceil(math.log2(len(f)))
    print(f"  {name:<14}: 符号数={len(f)} H={h:.3f} L={l:.3f} 定长={fixed} "
          f"节省={1-l/fixed:.1%}")

print("\n== 单符号退化情况 ==")
f1 = Counter("AAAA")
r1 = build_tree(f1); c1 = build_codes(r1)
print(f"  码表={c1}, 编码 'AAAA' = {encode('AAAA', c1)!r}, "
      f"解码={decode(encode('AAAA',c1), r1)!r}")

print("\n== 哈夫曼 vs 香农-范诺 / 算术编码 ==")
for line in (
    "  香农-范诺: 自顶向下二分，简单但不保证最优",
    "  哈夫曼   : 自底向上合并，整数码长下最优，L < H+1",
    "  算术编码 : 整条消息映射成一个区间小数，可突破 H+1，接近熵",
    "  ANS/FSE  : 现代压缩器（zstd、LZFSE）用的非对称数字系统",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  码表要随数据一起存（或双方约定静态码表，如 JPEG 标准表）",
    "  规范哈夫曼码 canonical 只需传码长即可重建码表，省空间",
    "  自适应哈夫曼在流式数据里动态更新频率",
    "  通常与 LZ77 等字典编码串联：先去重复再熵编码",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现规范哈夫曼码（按码长+符号排序生成），只存码长重建码表。
# 2. 给码流加长度头，验证带填充位的字节流解码。
# 3. 对比哈夫曼与算术编码在「高度偏斜」分布下的压缩率。
# 4. 思考：为什么前缀码可以「即时解码」而无需分隔符？
