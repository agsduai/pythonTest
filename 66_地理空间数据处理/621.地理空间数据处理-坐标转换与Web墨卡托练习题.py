# ===== 第621课：地理空间数据处理-坐标转换与Web墨卡托 =====
# 知识点：
#   - Web Mercator (EPSG:3857)：Google/OSM/高德等 Web 地图使用的投影
#   - 正算：x = R·λ，y = R·ln(tan(π/4 + φ/2))；纬度被限制在 ±85.0511°
#   - 反算：φ = 2·atan(exp(y/R)) - π/2；λ = x/R
#   - 墨卡托保角不保积：格陵兰看起来和非洲差不多大，实际差 14 倍
#   - 瓦片编号：z 级下 2^z × 2^z 张，256px；world_px = 256·2^z
#   - 像素/瓦片坐标原点在左上角，y 向下，与经纬度 y 方向相反
# 依赖：无（标准库）
import math

R = 6378137.0                       # Web Mercator 用的球半径
MAX_LAT = math.degrees(2 * math.atan(math.exp(math.pi)) - math.pi / 2)
TILE = 256


def lonlat_to_meters(lon, lat):
    lat = max(-MAX_LAT, min(MAX_LAT, lat))
    x = R * math.radians(lon)
    y = R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    return x, y


def meters_to_lonlat(x, y):
    return math.degrees(x / R), math.degrees(2 * math.atan(math.exp(y / R)) - math.pi / 2)


def lonlat_to_pixel(lon, lat, z):
    scale = TILE * (1 << z)
    x = (lon + 180) / 360 * scale
    s = math.sin(math.radians(lat))
    y = (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * scale
    return x, y


def pixel_to_tile(x, y):
    return int(x // TILE), int(y // TILE)


def tile_to_quadkey(x, y, z):
    """Bing/高德用的 quadkey：每级取 2bit 拼成四进制串。"""
    key = []
    for i in range(z, 0, -1):
        digit = 0
        mask = 1 << (i - 1)
        if x & mask:
            digit += 1
        if y & mask:
            digit += 2
        key.append(str(digit))
    return "".join(key)


print("== 投影边界 ==")
print(f"  Web Mercator 最大纬度: ±{MAX_LAT:.4f}°（超过会被 clamp）")

print("\n== 经纬度 -> 米 -> 经纬度 往返 ==")
for lon, lat in ((0, 0), (116.4074, 39.9042), (-74.006, 40.7128), (151.2, -33.86), (0, 85)):
    x, y = lonlat_to_meters(lon, lat)
    back = meters_to_lonlat(x, y)
    print(f"  ({lon:>9.4f},{lat:>7.4f}) -> ({x / 1000:>10.1f}km,{y / 1000:>9.1f}km) "
          f"-> ({back[0]:>9.4f},{back[1]:>7.4f}) 误差={abs(back[1] - lat):.2e}°")

print("\n== 全球范围 ==")
x0, y0 = lonlat_to_meters(-180, 0)
x1, y1 = lonlat_to_meters(180, 0)
print(f"  赤道周长投影: {(x1 - x0) / 1000:.1f} km（2πR = {2 * math.pi * R / 1000:.1f} km）")

print("\n== 面积畸变（保角不保积）==")
# 同经纬度跨度的网格，在不同纬度的「真实面积」与「投影面积」之比
def true_area(lon, lat, d=1.0):
    """1°×1° 球面带面积（近似）。"""
    return (math.pi / 180 * d) * (R ** 2) * (
        math.sin(math.radians(lat + d / 2)) - math.sin(math.radians(lat - d / 2))
    )

for lat in (0, 30, 60, 80):
    area = true_area(0, lat)
    proj_w = lonlat_to_meters(1, lat)[0] - lonlat_to_meters(0, lat)[0]
    proj_h = lonlat_to_meters(0, lat + 0.5)[1] - lonlat_to_meters(0, lat - 0.5)[1]
    proj_area = proj_w * proj_h
    print(f"  lat={lat:>2}°: 球面={area / 1e6:>8.1f}km² 投影={proj_area / 1e6:>10.1f}km² "
          f"放大={proj_area / area:>6.2f}×")

print("\n== 瓦片坐标（北京）==")
lon, lat = 116.4074, 39.9042
for z in (0, 1, 4, 10, 16):
    px, py = lonlat_to_pixel(lon, lat, z)
    tx, ty = pixel_to_tile(px, py)
    print(f"  z={z:>2}: 世界像素=({px:>12.1f},{py:>12.1f}) 瓦片=({tx:>6},{ty:>6}) "
          f"quadkey={tile_to_quadkey(tx, ty, z)}")

print("\n== 反算瓦片覆盖的经纬度范围 ==")
def tile_bounds(tx, ty, z):
    n = 1 << z
    lon1 = tx / n * 360 - 180
    lon2 = (tx + 1) / n * 360 - 180
    lat1 = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * ty / n))))
    lat2 = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (ty + 1) / n))))
    return lon1, lat2, lon2, lat1      # minx,miny,maxx,maxy

for z in (2, 8, 14):
    px, py = lonlat_to_pixel(lon, lat, z)
    tx, ty = pixel_to_tile(px, py)
    b = tile_bounds(tx, ty, z)
    print(f"  z={z:>2} tile({tx},{ty}): lon [{b[0]:.4f},{b[2]:.4f}] "
          f"lat [{b[1]:.4f},{b[3]:.4f}] 跨度={b[2]-b[0]:.4f}°")

print("\n== 为什么极地不适合墨卡托 ==")
print("  y 在纬度趋近 90° 时趋于无穷，必须人为截断到 85.05°")
print("  极区应改用极方位投影（EPSG:3413 / 3031）")

# ===== 练习题 =====
# 1. 实现 quadkey_to_tile(key)，把四进制串还原成 (tx, ty, z)。
# 2. 计算 z=12 时北京所在瓦片四角的经纬度，并画出一个 bbox。
# 3. 写一个函数返回覆盖给定 bbox 的所有瓦片坐标列表。
# 4. 思考：为什么 Web 地图普遍选墨卡托而不是等积投影？
