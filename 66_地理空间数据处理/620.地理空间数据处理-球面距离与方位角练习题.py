# ===== 第620课：地理空间数据处理-球面距离与方位角 =====
# 知识点：
#   - Haversine：用半正矢公式算球面大圆距离，短中距离数值稳定
#   - 余弦定理法：acos(sinφ1sinφ2 + cosφ1cosφ2cosΔλ)，短距离易精度损失
#   - Vincenty（椭球）更精确但迭代复杂；本课题用球形近似足够
#   - 初始方位角 bearing：从正北顺时针 0~360°，用 atan2 求
#   - 等距航线中途点 / 给定起点+距离+方位求终点（destination point）
#   - 平面勾股距离只在小范围（<1km）可近似，且要按 cos(lat) 缩放经度
# 依赖：无（标准库）
import math

EARTH_R = 6371008.8

CITIES = {
    "北京": (116.4074, 39.9042),
    "上海": (121.4737, 31.2304),
    "广州": (113.2644, 23.1291),
    "成都": (104.0665, 30.5728),
    "纽约": (-74.0060, 40.7128),
    "伦敦": (-0.1276, 51.5072),
    "悉尼": (151.2093, -33.8688),
}


def haversine(a, b, r=EARTH_R) -> float:
    """a,b 为 (lon, lat)，返回米。"""
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    dlon, dlat = lon2 - lon1, lat2 - lat1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def cos_law(a, b, r=EARTH_R) -> float:
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    v = (math.sin(lat1) * math.sin(lat2) +
         math.cos(lat1) * math.cos(lat2) * math.cos(lon2 - lon1))
    return r * math.acos(max(-1.0, min(1.0, v)))


def bearing(a, b) -> float:
    """初始方位角，正北为 0，顺时针 0~360。"""
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = (math.cos(lat1) * math.sin(lat2) -
         math.sin(lat1) * math.cos(lat2) * math.cos(dlon))
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def destination(a, dist_m: float, brng_deg: float, r=EARTH_R):
    """从 a 沿方位角走 dist_m 米，返回 (lon, lat)。"""
    lon1, lat1 = map(math.radians, a)
    theta = math.radians(brng_deg)
    d = dist_m / r
    lat2 = math.asin(math.sin(lat1) * math.cos(d) +
                     math.cos(lat1) * math.sin(d) * math.cos(theta))
    lon2 = lon1 + math.atan2(
        math.sin(theta) * math.sin(d) * math.cos(lat1),
        math.cos(d) - math.sin(lat1) * math.sin(lat2),
    )
    return math.degrees(lon2), math.degrees(lat2)


def compass(deg: float) -> str:
    dirs = ("北", "东北", "东", "东南", "南", "西南", "西", "西北")
    return dirs[round(deg / 45) % 8]


print("== 城市间大圆距离 ==")
pairs = [("北京", "上海"), ("北京", "广州"), ("北京", "成都"),
         ("北京", "纽约"), ("伦敦", "悉尼")]
for x, y in pairs:
    d1, d2 = haversine(CITIES[x], CITIES[y]), cos_law(CITIES[x], CITIES[y])
    print(f"  {x}->{y}: {d1 / 1000:>9.1f} km  "
          f"余弦法={d2 / 1000:>9.1f} km  差={abs(d1 - d2):.3f} m  "
          f"方位={bearing(CITIES[x], CITIES[y]):6.1f}°({compass(bearing(CITIES[x], CITIES[y]))})")

print("\n== 极短距离：两种公式的数值稳定性 ==")
a = (116.4074, 39.9042)
for meters in (0, 0.1, 1, 10, 100):
    b = destination(a, meters, 90)
    print(f"  {meters:>6.1f}m: haversine={haversine(a, b):>9.4f}m  "
          f"cos_law={cos_law(a, b):>9.4f}m")

print("\n== 出发->到达 往返验证 ==")
for brng in (0, 45, 90, 180, 270, 315):
    b = destination(a, 100000, brng)
    print(f"  方位 {brng:>3}° 走 100km -> ({b[0]:.4f}, {b[1]:.4f}); "
          f"回算距离={haversine(a, b) / 1000:.3f}km  回算方位={bearing(a, b):.1f}°")

print("\n== 平面近似 vs 球面（小范围）==")
def planar(a, b) -> float:
    lat_km = math.pi * EARTH_R / 180 / 1000
    dx = (b[0] - a[0]) * lat_km * math.cos(math.radians((a[1] + b[1]) / 2)) * 1000
    dy = (b[1] - a[1]) * lat_km * 1000
    return math.hypot(dx, dy)

for km in (0.1, 1, 10, 100, 1000):
    b = destination(a, km * 1000, 60)
    p, h = planar(a, b), haversine(a, b)
    print(f"  {km:>6}km: 平面={p / 1000:>8.3f} 球面={h / 1000:>8.3f} "
          f"误差={(p - h) / h:+.2%}")

print("\n== 最近城市（暴力检索）==")
target = (117.2, 39.1)
ranked = sorted(CITIES.items(), key=lambda kv: haversine(target, kv[1]))
for name, _ in ranked[:3]:
    print(f"  {name}: {haversine(target, CITIES[name]) / 1000:.1f} km")

# ===== 练习题 =====
# 1. 实现 midpoint(a, b) 求球面中点，并验证到两端距离相等。
# 2. 计算「北京->纽约」大圆航线经过的几个中途点（等分 10 段）。
# 3. 用球面三角形面积公式估算北京/上海/广州三点围成的面积。
# 4. 思考：为什么跨洋航线在平面地图上画成弧线，而不是直线？
