# ===== 第619课：地理空间数据处理-经纬度与坐标基础 =====
# 知识点：
#   - 纬度 latitude(-90~90)，经度 longitude(-180~180)；注意顺序常写成 (lon, lat)
#   - WGS84：GPS 使用的椭球基准；GCJ-02（火星坐标）是中国大陆偏移加密坐标系
#   - 度分秒 DMS <-> 十进制度 DD：dd = d + m/60 + s/3600
#   - 每个坐标系的数据必须先统一再计算，混用会产生数百米误差
#   - 经纬度是球面坐标，不能直接当平面 xy 做加减或算面积
#   - 常见坑：跨 180° 经线（国际日期变更线）、极区经度退化
# 依赖：无（标准库）
from dataclasses import dataclass

EARTH_R = 6371008.8          # WGS84 平均半径（米）

@dataclass(frozen=True)
class Point:
    lon: float
    lat: float

    def __post_init__(self):
        if not -180 <= self.lon <= 180 or not -90 <= self.lat <= 90:
            raise ValueError(f"非法经纬度: {self}")

    def dms(self) -> str:
        return f"{dd_to_dms(self.lat, 'NS')} {dd_to_dms(self.lon, 'EW')}"


def dms_to_dd(d: int, m: int, s: float, hemi: str) -> float:
    """度分秒 + 半球标志 -> 十进制度。"""
    sign = -1 if hemi.upper() in "SW" else 1
    return sign * (abs(d) + m / 60 + s / 3600)


def dd_to_dms(dd: float, hemispheres: str) -> str:
    """十进制度 -> 度°分′秒″ + 半球字母。"""
    hemi = hemispheres[0] if dd >= 0 else hemispheres[1]
    v = abs(dd)
    d = int(v)
    m = int((v - d) * 60)
    s = (v - d - m / 60) * 3600
    return f"{d}°{m:02d}′{s:05.2f}″{hemi}"


print("== 构造与校验 ==")
beijing = Point(116.4074, 39.9042)
print("  北京:", beijing)
try:
    Point(200, 30)
except ValueError as e:
    print("  越界校验:", e)

print("\n== DMS <-> DD ==")
for d, m, s, hemi in ((39, 54, 15.12, "N"), (116, 24, 26.64, "E"),
                       (22, 16, 42.0, "S"), (114, 10, 30.0, "W")):
    dd = dms_to_dd(d, m, s, hemi)
    print(f"  {d}°{m}′{s}″{hemi} -> {dd: .6f}° -> {dd_to_dms(dd, 'NS' if hemi in 'NS' else 'EW')}")

print("\n== 十进制度格式化 ==")
print("  北京 DMS:", beijing.dms())
for p in (Point(121.4737, 31.2304), Point(-74.0060, 40.7128), Point(0, 0)):
    print(f"  {p.lon:>10.4f}, {p.lat:>9.4f} -> {p.dms()}")

print("\n== 1 度大约多长 ==")
import math
lat = 39.9
lat_km = math.pi * EARTH_R / 180 / 1000
lon_km = lat_km * math.cos(math.radians(lat))
print(f"  纬度 1° ≈ {lat_km:.2f} km（各处几乎相同）")
print(f"  纬度 {lat}° 处经度 1° ≈ {lon_km:.2f} km（随纬度 cos 收缩）")
for la in (0, 30, 60, 80, 89):
    print(f"    lat={la:>2}°: 1° 经度 ≈ {lat_km * math.cos(math.radians(la)):.2f} km")

print("\n== 跨 180° 经线的经度差 ==")
def lon_diff(a: float, b: float) -> float:
    """返回 -180~180 的最短经度差。"""
    d = (b - a + 180) % 360 - 180
    return d

for a, b in ((170, -170), (-179, 179), (10, 20), (0, 181)):
    print(f"  {a:>5} -> {b:>5}: 最短差 = {lon_diff(a, b):>7.1f}°")

print("\n== 坐标系混用的误差量级 ==")
print("  WGS84(GPS) 与 GCJ-02(火星) 在中国大陆相差约 300~600 米")
print("  BD-09(百度) 在 GCJ-02 上又叠一层偏移")
print("  同一份数据里绝不能混用；转换需专门的偏置表/算法")

print("\n== 常见数据顺序 ==")
for line in [
    "GeoJSON: [lon, lat]（经度在前）",
    "很多地图 API: lat, lon（纬度在前）",
    "numpy/数组: 通常是 (x=lon, y=lat)",
    "入库前统一字段名，别用二元组裸传",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 parse_dms("39°54′15.12″N") 返回浮点数。
# 2. 写一个 normalize_lon(lon)，把任意经度折到 [-180, 180)。
# 3. 给定左上/右下两点，判断一个点是否落在经纬度矩形内（考虑跨 180°）。
# 4. 思考：为什么高纬度地区「1°×1° 的网格」实际面积比赤道小得多？
