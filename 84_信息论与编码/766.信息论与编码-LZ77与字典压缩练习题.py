# ===== 第766课：信息论与编码-LZ77 与字典压缩 =====
# 知识点：
#   - LZ77：用「(距离, 长度, 下一个字符)」三元组指向之前出现过的串，消除重复
#   - 滑动窗口：只在最近 W 字节里找最长匹配，控制内存与解码一致性
#   - LZ78/LZW：显式维护字典，输出字典索引；解码方能同步重建字典
#   - 与哈夫曼互补：LZ 去「结构冗余」，熵编码去「统计冗余」（ZIP = LZ77 + Huffman）
#   - 压缩比、压缩/解压耗时、窗口大小是工程三要素
#   - 本课实现朴素 LZ77 编解码 + LZW，验证无损往返
# 依赖：无（标准库）
import time


def lz77_encode(data, window=4096, max_match=18):
    """朴素 LZ77：逐位置在窗口里找最长匹配，输出 (dist, length, next_char)。"""
    out = []
    i, n = 0, len(data)
    while i < n:
        start = max(0, i - window)
        best_len, best_dist = 0, 0
        # 从最近的位置往回找（越近越常见）
        for j in range(i-1, start-1, -1):
            k = 0
            while (k < max_match and i+k < n and data[j+k] == data[i+k]):
                k += 1
            if k > best_len:
                best_len, best_dist = k, i-j
                if k == max_match:
                    break
        if best_len >= 3:
            nxt = data[i+best_len] if i+best_len < n else ""
            out.append((best_dist, best_len, nxt))
            i += best_len + (1 if nxt else 0)
        else:
            out.append((0, 0, data[i]))
            i += 1
    return out


def lz77_decode(tokens):
    out = []
    for dist, length, nxt in tokens:
        if length:
            start = len(out) - dist
            for k in range(length):
                out.append(out[start+k])     # 允许重叠复制
        if nxt:
            out.append(nxt)
    return "".join(out)


def lzw_encode(data):
    """LZW：字典初始化为消息里出现的所有单字符（支持中文/Unicode）。"""
    alphabet = sorted(set(data))
    dictionary = {ch: i for i, ch in enumerate(alphabet)}
    next_code = len(alphabet)
    w, out = "", []
    for c in data:
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            out.append(dictionary[w])
            dictionary[wc] = next_code; next_code += 1
            w = c
    if w:
        out.append(dictionary[w])
    return out, alphabet


def lzw_decode(codes, alphabet):
    dictionary = {i: ch for i, ch in enumerate(alphabet)}
    next_code = len(alphabet)
    if not codes: return ""
    w = dictionary[codes[0]]
    out = [w]
    for code in codes[1:]:
        if code in dictionary:
            entry = dictionary[code]
        elif code == next_code:            # KwKwK 特例
            entry = w + w[0]
        else:
            raise ValueError("非法码流")
        out.append(entry)
        dictionary[next_code] = w + entry[0]
        next_code += 1
        w = entry
    return "".join(out)


print("== LZ77 编解码 ==")
texts = [
    "ABABABABABABABAB",
    "TOBEORNOTTOBEORTOBEORNOT",
    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "The quick brown fox jumps over the lazy dog. " * 5,
]
for t in texts:
    toks = lz77_encode(t, window=64, max_match=12)
    back = lz77_decode(toks)
    raw = len(t.encode("utf-8"))
    # 粗略：每个 token 约 3 字节（教学估算，未做位打包）
    est = len(toks) * 3
    print(f"  原文 {raw:>4}B -> {len(toks):>3} 个 token（约 {est}B） "
          f"往返={back == t}  前 4 token={toks[:4]}")

print("\n== 窗口大小的影响 ==")
t = "ABCD" * 40 + "XYZ" + "ABCD" * 40
for W in (16, 64, 256, 1024):
    toks = lz77_encode(t, window=W, max_match=18)
    print(f"  window={W:>5}: token 数={len(toks):>4} 往返={lz77_decode(toks)==t}")
print("  窗口要能覆盖重复串的距离，太大会拖慢搜索")

print("\n== 允许重叠复制（LZ77 的关键细节）==")
# 用 "ABABAB..." 验证：匹配距离 2、长度可以超过距离
t = "AB" * 20
toks = lz77_encode(t, window=64, max_match=12)
print(f"  'AB'*20 的 token: {toks}")
print(f"  解码一致: {lz77_decode(toks) == t}")
print("  复制时逐字节读 out[start+k]，天然支持长度 > 距离")

print("\n== LZW 编解码 ==")
for t in ("TOBEORNOTTOBEORTOBEORNOT", "aaaaabaaaaacaaaaad", "hello hello hello"):
    codes, alphabet = lzw_encode(t)
    back = lzw_decode(codes, alphabet)
    print(f"  {t[:28]!r:<32} -> {len(codes)} 个码字, 往返={back==t}, "
          f"初始字母表 {len(alphabet)} 项, 字典增长到 {len(alphabet)+len(codes)} 项")

print("\n== 压缩率与耗时 ==")
t = ("Python 是一门优雅的语言。" * 200)
t0=time.perf_counter(); lz = lz77_encode(t, window=4096, max_match=18); t1=time.perf_counter()
lzw, alpha = lzw_encode(t); t2=time.perf_counter()
back1, back2 = lz77_decode(lz), lzw_decode(lzw, alpha)
print(f"  原文 {len(t.encode('utf-8'))}B, LZ77 {len(lz)} token ({t1-t0:.3f}s), "
      f"LZW {len(lzw)} 码字 ({t2-t1:.3f}s)")
print(f"  两者均无损: {back1 == t and back2 == t}")

print("\n== LZ77 vs 哈夫曼（分工不同）==")
for line in (
    "  哈夫曼: 利用「符号频率不均」，单个字符独立编码（第764课）",
    "  LZ77  : 利用「子串重复」，一次引用一整段",
    "  单独用哈夫曼压 'ABABAB...' 收益有限；LZ 能压到极少 token",
    "  DEFLATE(ZIP/gzip) = LZ77 + 哈夫曼，先去结构冗余再去统计冗余",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  朴素最长匹配 O(n·W·L)；真实实现用哈希链 / 二叉搜索树加速",
    "  贪心最长匹配不保证全局最优，可用 lazy matching 改善",
    "  窗口 32KB（DEFLATE）、LZ4 追求极速、zstd 用 FSE 熵编码",
    "  解压端不需要存字典（LZ77）或与压缩端同步重建（LZW）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给 LZ77 增加哈希链索引，把最长匹配从 O(n·W) 降到近似 O(n)。
# 2. 把 LZ77 token 再做哈夫曼编码（输出字面量/长度/距离三张码表）。
# 3. 实现 LZ78 与 LZW 的对比，观察字典增长差异。
# 4. 思考：为什么 LZ77 的解码必须允许「重叠复制」？
