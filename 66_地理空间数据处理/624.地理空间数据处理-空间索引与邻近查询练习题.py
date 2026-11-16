# ===== 第624课：地理空间数据处理-空间索引与邻近查询 =====
# 知识点：
#   - 暴力 KNN：O(n)，数据量小时够用；百万级 POI 必须建索引
#   - 网格索引：把空间切成固定格子，只查目标格及其邻格，均摊 O(1)
#   - 网格大小要按「查询半径」选：格子太大候选多，太小邻格数暴涨
#   - Geohash：把经纬度交错二分编码成 base32 字符串，前缀相同即邻近
#   - Geohash 的边界问题：相邻两点可能落在完全不同前缀，需查 8 个邻居
#   - 生产常用 R-tree / QuadTree / H3 / S2；本课手写网格与简化 geohash
# 依赖：无（标准库）
import math
from collections import defaultdict

EARTH_R = 6371008.8
BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"


def haversine(a, b):
    lon1, lat1, lon2, lat2 = map(math.radians, (*a, *b))
    h = (math.sin((lat2 - lat1) / 2) ** 2 +
         math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 2 * EARTH_R * math.asin(math.sqrt(h))


class GridIndex:
    """固定经纬度网格（非等积，教学用）。"""

    def __init__(self, cell_deg: float):
        self.cell = cell_deg
        self.buckets = defaultdict(list)

    def key(self, lon, lat):
        return math.floor(lon / self.cell), math.floor(lat / self.cell)

    def insert(self, name, lon, lat):
        self.buckets[self.key(lon, lat)].append((name, (lon, lat)))

    def candidates(self, lon, lat, rings=1):
        cx, cy = self.key(lon, lat)
        for dx in range(-rings, rings + 1):
            for dy in range(-rings, rings + 1):
                yield from self.buckets.get((cx + dx, cy + dy), ())

    def knn(self, lon, lat, k=3, max_rings=8):
        """自动扩大邻格范围，直到凑够 k 个候选（避免细网格漏查）。"""
        for rings in range(1, max_rings + 1):
            cands = list(self.candidates(lon, lat, rings))
            if len(cands) >= k:
                return sorted(cands, key=lambda item: haversine((lon, lat), item[1]))[:k]
        return sorted(cands, key=lambda item: haversine((lon, lat), item[1]))[:k]

    def within(self, lon, lat, radius_m):
        rings = max(1, math.ceil(radius_m / 111000 / self.cell))
        return [(n, p, haversine((lon, lat), p))
                for n, p in self.candidates(lon, lat, rings)
                if haversine((lon, lat), p) <= radius_m]


def geohash_encode(lon, lat, precision=6):
    """经纬度 -> base32 geohash（交错二分）。"""
    lon_rng, lat_rng = [-180.0, 180.0], [-90.0, 90.0]
    bits, out = [], []
    is_lon = True
    for _ in range(precision * 5):
        lo, hi = (lon_rng if is_lon else lat_rng)
        mid = (lo + hi) / 2
        val = lon if is_lon else lat
        if val >= mid:
            bits.append(1)
            (lon_rng if is_lon else lat_rng)[0] = mid
        else:
            bits.append(0)
            (lon_rng if is_lon else lat_rng)[1] = mid
        is_lon = not is_lon
        if len(bits) == 5:
            idx = 0
            for b in bits:
                idx = (idx << 1) | b
            out.append(BASE32[idx])
            bits = []
    return "".join(out)


def geohash_decode(code):
    lon_rng, lat_rng = [-180.0, 180.0], [-90.0, 90.0]
    is_lon = True
    for ch in code:
        if ch not in BASE32:
            raise ValueError(f"非法 geohash 字符: {ch}")
        v = BASE32.index(ch)
        for i in range(4, -1, -1):
            bit = (v >> i) & 1
            rng = lon_rng if is_lon else lat_rng
            mid = (rng[0] + rng[1]) / 2
            rng[1 - bit] = mid      # bit=1 取右半(改下界 idx0)，bit=0 取左半(改上界 idx1)
            is_lon = not is_lon
    return ((lon_rng[0] + lon_rng[1]) / 2, (lat_rng[0] + lat_rng[1]) / 2)


POIS = [
    ("故宫", 116.397, 39.918), ("天安门", 116.397, 39.908),
    ("景山", 116.396, 39.925), ("王府井", 116.411, 39.914),
    ("北海", 116.389, 39.928), ("国贸", 116.461, 39.909),
    ("西单", 116.374, 39.907), ("中关村", 116.316, 39.982),
]

print("== 暴力 KNN（基线）==")
query = (116.400, 39.915)
brute = sorted(POIS, key=lambda p: haversine(query, (p[1], p[2])))
for name, lon, lat in brute[:3]:
    print(f"  {name:<6} {haversine(query, (lon, lat)):>8.0f} m")

print("\n== 网格索引 ==")
for cell in (0.005, 0.02, 0.1):
    idx = GridIndex(cell)
    for name, lon, lat in POIS:
        idx.insert(name, lon, lat)
    near = idx.knn(*query, k=3)
    # 观察自动扩展：从 rings=1 起，直到候选数 >= k
    rings_used = next(r for r in range(1, 9)
                      if len(list(idx.candidates(*query, r))) >= 3)
    print(f"  cell={cell:<6} 桶数={len(idx.buckets):>2} KNN={[n for n, _ in near]} "
          f"自动扩展到 rings={rings_used}，候选数={len(list(idx.candidates(*query, rings_used)))}")

print("\n== 半径查询 ==")
idx = GridIndex(0.01)
for name, lon, lat in POIS:
    idx.insert(name, lon, lat)
for r in (500, 1500, 5000):
    hits = idx.within(*query, r)
    print(f"  {r:>5}m 内: {[n for n, _, _ in hits]}")

print("\n== Geohash 编解码 ==")
for name, lon, lat in POIS[:5]:
    code = geohash_encode(lon, lat, 6)
    back = geohash_decode(code)
    print(f"  {name:<6} ({lon:.3f},{lat:.3f}) -> {code} -> ({back[0]:.3f},{back[1]:.3f}) "
          f"误差={haversine((lon, lat), back):.0f}m")

print("\n== 前缀共享即邻近 ==")
c1 = geohash_encode(116.397, 39.918, 6)
c2 = geohash_encode(116.3975, 39.9182, 6)
c3 = geohash_encode(121.473, 31.230, 6)
common = 0
for a, b in zip(c1, c2):
    if a == b:
        common += 1
    else:
        break
print(f"  邻近两点: {c1} / {c2} 公共前缀={common} 字符")
print(f"  遥远两点: {c1} / {c3} 首字符相同={c1[0] == c3[0]}")
for prec in (1, 3, 5, 7, 9):
    code = geohash_encode(*query, prec)
    lo, hi = geohash_decode(code), geohash_decode(code)
    print(f"  precision={prec}: {code:<10} 中心≈({lo[0]:.2f},{lo[1]:.2f})")

print("\n== 边界问题 ==")
print("  一个点恰好在格子分界线两侧时，geohash 前缀可能完全不同")
print("  因此邻近查询要同时检索自身 + 8 个邻居格（或扩大网格 rings）")

print("\n== 索引选型建议 ==")
for line in [
    "点数据、半径查询为主 -> 网格 / geohash / H3",
    "线面数据、范围重叠 -> R-tree（SQLite R*Tree、PostGIS GiST）",
    "全球均匀分级 -> S2 / H3 六边形，避免高纬度畸变",
    "内存里几千条以内，暴力 KNN 往往比建索引更简单更快",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给 GridIndex 增加 remove(name) 与自动扩展查询半径直到凑够 k 个结果。
# 2. 实现 geohash 邻居计算（8 个方向），解决边界漏查问题。
# 3. 用不同 cell 大小跑 10000 个随机点，对比查询耗时与候选数量。
# 4. 思考：为什么经纬度网格在高纬度地区不是「等面积」网格？H3 如何缓解？
