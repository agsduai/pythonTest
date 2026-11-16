# ===== 第798课：流式算法与数据摘要-HyperLogLog基数估计 =====
# 知识点：
#   - 基数估计 cardinality：流里有多少个「不同」元素（UV 统计）
#   - 精确方案需存所有键：10 亿 UV 要 GB 级内存
#   - HyperLogLog (HLL)：只存 m 个寄存器，标准误差 ≈ 1.04/√m
#   - 原理：哈希值的「前导零个数」——前导零多说明哈希值落在很小的概率区间
#   - 每个寄存器记录「该桶里见过的最大前导零数」；用调和平均合并
#   - 16384 个寄存器（m=2^14）→ 误差 0.81%，内存仅 ~12KB
#   - HLL 天然可合并：寄存器逐个取 max 即可，跨分片/跨天聚合无痛
# 依赖：无（标准库）
import hashlib
import math


def _hash64(s):
    return int.from_bytes(hashlib.md5(str(s).encode()).digest()[:8], "big")


class HyperLogLog:
    def __init__(self, p=14):
        self.p = p
        self.m = 1 << p                       # 寄存器个数（2^14 = 16384）
        self.registers = [0] * self.m

    def _index_and_bits(self, item):
        hv = _hash64(item)
        bucket = hv >> (64 - self.p)          # 前 p 位选桶
        rest = hv & ((1 << (64 - self.p)) - 1)
        # 剩余位中前导零的个数 + 1（最多 64-p）
        leading = 1
        for i in range(63 - self.p, -1, -1):
            if rest & (1 << i):
                break
            leading += 1
        return bucket, leading

    def add(self, item):
        bucket, leading = self._index_and_bits(item)
        if leading > self.registers[bucket]:
            self.registers[bucket] = leading

    def count(self):
        m = self.m
        raw = sum(2.0 ** -r for r in self.registers)   # 调和平均的核心项
        alpha = self._alpha(m)
        est = alpha * m * m / raw
        # 小基数修正：空寄存器多时用线性计数
        zeros = self.registers.count(0)
        if est <= 2.5 * m and zeros > 0:
            est = m * math.log(m / zeros)
        return est

    @staticmethod
    def _alpha(m):
        if m == 16: return 0.673
        if m == 32: return 0.697
        if m == 64: return 0.709
        if m == 128: return 0.7153
        return 0.7213 / (1 + 1.079 / m)

    def merge(self, other):
        for i, r in enumerate(other.registers):
            if r > self.registers[i]:
                self.registers[i] = r

    def memory_bytes(self):
        return self.m                          # 每寄存器 1 字节（6bit 实际够用）


def exact_distinct(stream):
    return len(set(stream))


print("== 原理演示：前导零与桶 ==")
hll = HyperLogLog(p=4)                         # 16 个寄存器，便于观察
for item in ("alice", "bob", "carol", "alice"):
    bucket, leading = hll._index_and_bits(item)
    hv = _hash64(item)
    print(f"  {item!r:<8} 哈希={hv:016x}  桶={bucket:>2}  前导零+1={leading}")
    hll.add(item)
print(f"  寄存器: {hll.registers}")
print(f"  估计基数: {hll.count():.1f}（真实 3）——小基数用线性计数修正")

print("\n== 误差与寄存器数 p 的关系 ==")
N = 500000
stream = [f"user{i % 100000}" for i in range(N)]     # 真实基数 100000
TRUTH = 100000
print(f"  流长度={N:,}，真实不同值={TRUTH:,}")
print(f"  {'p':<4}{'寄存器':>8}{'内存':>10}{'理论误差':>12}{'实测误差':>12}")
for p in (4, 8, 10, 12, 14, 16):
    h = HyperLogLog(p)
    for x in stream:
        h.add(x)
    est = h.count()
    err = abs(est - TRUTH) / TRUTH
    theory = 1.04 / math.sqrt(2 ** p)
    print(f"  {p:<4}{2**p:>8}{h.memory_bytes()/1024:>8.1f}K{theory:>11.2%}"
          f"{err:>12.2%}")

print("\n== 合并：跨天/跨分片 UV 去重 ==")
h_day1, h_day2 = HyperLogLog(p=14), HyperLogLog(p=14)
overlap = [f"user{i}" for i in range(60000)]
day1 = overlap[:40000] + [f"new{i}" for i in range(20000)]
day2 = overlap[20000:] + [f"fresh{i}" for i in range(15000)]
for x in day1: h_day1.add(x)
for x in day2: h_day2.add(x)
merged = HyperLogLog(p=14)
merged.merge(h_day1); merged.merge(h_day2)
exact_total = len(set(day1 + day2))
print(f"  Day1 UV≈{h_day1.count():.0f}  Day2 UV≈{h_day2.count():.0f}")
print(f"  合并后 UV≈{merged.count():.0f}（精确={exact_total}）")
print(f"  内存：两个 HLL 各 {h_day1.memory_bytes()/1024:.0f}KB，"
      f"精确统计需要 {exact_total*10/1024/1024:.1f}MB")
print("  合并 = 寄存器逐个取 max，天然支持分布式")

print("\n== 与精确 Set 的对比 ==")
print(f"  {'方案':<16}{'内存(100万UV)':<20}{'误差':<12}{'可合并'}")
for row in (("精确 set", "≈50-80 MB", "0", "是(集合并)"),
            ("HLL p=14", "≈16 KB", "±0.8%", "是(取max)"),
            ("HLL p=16", "≈64 KB", "±0.4%", "是")):
    print(f"  {row[0]:<16}{row[1]:<20}{row[2]:<12}{row[3]}")

print("\n== 工程要点 ==")
for line in [
    "  Redis 的 PFADD/PFCOUNT 就是 HLL；Google 的 paper 使它流行",
    "  稀疏编码：小基数时只存非零桶，节省内存",
    "  HLL++：改进初始区间的估计，小基数误差更小",
    "  用 6 bit 存寄存器（最大值 63+1），16384 个寄存器只需 12KB",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 HLL 的「交集估计」：I(A∩B) ≈ (|A|+|B|-|A∪B|)，实测误差。
# 2. 用差分哈希（d-bit hashing）改进交集估计精度。
# 3. 对比 HLL 与 LinearCounting 在 1000 元素小基数上的误差。
# 4. 思考：为什么用「调和平均」而不是「算术平均」合并寄存器？
