# ===== 第425课：数据结构进阶-布隆过滤器 =====
# 知识点：
#   - 布隆过滤器：用“位数组 + 多个哈希”判断“可能存在 / 一定不存在”
#   - 只支持 add 和 contains，不支持删除（标准版）
#   - 有假阳性（false positive），但绝无假阴性 —— 说没有就一定没有
#   - 空间极省：100 万条只占几百 KB；适合缓存穿透、爬虫去重、黑名单
#   - 参数：m 位数组大小、k 哈希个数；假阳性率 ≈ (1 - e^(-kn/m))^k
import hashlib
import math


class BloomFilter:

    def __init__(self, size: int = 100_000, hashes: int = 5):
        if size <= 0 or hashes <= 0:
            raise ValueError("size 与 hashes 必须为正")
        self.size = size
        self.hashes = hashes
        self.bits = bytearray((size + 7) // 8)
        self.count = 0

    def _positions(self, item: str):
        """用不同盐的 SHA-256 生成 k 个位置（工程上比多个哈希函数简单）。"""
        for seed in range(self.hashes):
            digest = hashlib.sha256(f"{seed}:{item}".encode("utf-8")).digest()
            yield int.from_bytes(digest[:8], "big") % self.size

    def _set(self, pos: int):
        self.bits[pos // 8] |= 1 << (pos % 8)

    def _get(self, pos: int) -> bool:
        return bool(self.bits[pos // 8] & (1 << (pos % 8)))

    def add(self, item: str):
        for pos in self._positions(item):
            self._set(pos)
        self.count += 1

    def __contains__(self, item: str) -> bool:
        return all(self._get(pos) for pos in self._positions(item))

    def false_positive_rate(self) -> float:
        """理论假阳性率。"""
        k, n, m = self.hashes, self.count, self.size
        return (1 - math.exp(-k * n / m)) ** k

    def usage(self) -> float:
        used = sum(bin(b).count("1") for b in self.bits)
        return used / self.size


bf = BloomFilter(size=10_000, hashes=3)

# ---- 加入 1000 个“已访问 URL” ----
for i in range(1000):
    bf.add(f"https://example.com/page/{i}")

print("== 已加入的元素：全部命中（无假阴性）==")
sample_hits = all(f"https://example.com/page/{i}" in bf for i in range(1000))
print("  1000 个全部 contains = True：", sample_hits)

# ---- 测试 1000 个未加入的元素：统计假阳性 ----
fp = sum(f"https://other.com/{i}" in bf for i in range(1000))
print("\n== 未加入的元素 ==")
print(f"  1000 个中误判：{fp} 个（假阳性率 {fp / 1000:.2%}）")
print(f"  理论假阳性率：{bf.false_positive_rate():.2%}")
print(f"  位数组占用：{bf.usage():.1%}")

# ---- 参数影响：位数组越大、哈希越多，假阳性越低 ----
print("\n== 参数对比（同样 1000 条）==")
for size, k in [(2_000, 3), (10_000, 3), (10_000, 8), (50_000, 5)]:
    test = BloomFilter(size, k)
    for i in range(1000):
        test.add(f"item-{i}")
    fp = sum(f"miss-{i}" in test for i in range(1000))
    print(f"  size={size:6d} k={k} → 假阳性 {fp / 1000:.2%}，理论 {test.false_positive_rate():.2%}")

# ---- 实战：缓存穿透防护 ----
print("\n== 缓存穿透防护流程 ==")
known_ids = {"u1", "u2", "u3"}
bf2 = BloomFilter(size=1000, hashes=3)
for uid in known_ids:
    bf2.add(uid)

def query_user(uid):
    if uid not in bf2:
        return "直接拒绝：布隆过滤器说一定不存在"
    if uid in known_ids:
        return f"命中用户 {uid}"
    return "可能有（假阳性），继续查库确认"

for uid in ("u1", "u9"):
    print(f"  查询 {uid} → {query_user(uid)}")

# ===== 练习题 =====
# 1. 实现 counting Bloom filter（计数位）以支持删除。
# 2. 用布隆过滤器给爬虫 URL 去重，内存相比 set 节省多少？
# 3. 计算：允许 1% 假阳性、存 100 万条，m 和 k 该取多少？
# 4. 思考：为什么布隆过滤器“说没有”绝对可信？
