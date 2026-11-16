# ===== 第622课：地理空间数据处理-GeoJSON与几何对象 =====
# 知识点：
#   - GeoJSON (RFC 7946)：Point / LineString / Polygon / Multi* / GeometryCollection
#   - 坐标一律 [lon, lat]（可带第三维高程）；Feature 包 geometry + properties
#   - FeatureCollection 是 features 数组，可带 bbox 与 crs（RFC 默认 WGS84）
#   - Polygon 的环必须闭合（首点 == 末点），外环逆时针、内环（洞）顺时针
#   - bbox 计算要处理跨 180° 经线；简单场景直接 min/max 即可
#   - 用 json 模块读写；几何计算交给专门库（shapely），本课手写基础校验
# 依赖：无（标准库）
import json
import tempfile
from pathlib import Path

fc = {
    "type": "FeatureCollection",
    "features": [
        {"type": "Feature", "properties": {"name": "北京", "pop": 2154},
         "geometry": {"type": "Point", "coordinates": [116.4074, 39.9042]}},
        {"type": "Feature", "properties": {"name": "上海", "pop": 2487},
         "geometry": {"type": "Point", "coordinates": [121.4737, 31.2304]}},
        {"type": "Feature", "properties": {"name": "高铁示意", "mode": "rail"},
         "geometry": {"type": "LineString", "coordinates": [
             [116.4074, 39.9042], [117.2, 39.1], [118.8, 32.1], [121.4737, 31.2304]]}},
        {"type": "Feature", "properties": {"name": "示例区域"},
         "geometry": {"type": "Polygon", "coordinates": [[
             [116.0, 39.5], [117.0, 39.5], [117.0, 40.5], [116.0, 40.5], [116.0, 39.5]]]}},
    ],
}


def coord_stream(geom):
    """递归产出几何里的所有坐标点。"""
    t = geom["type"]
    if t == "Point":
        yield geom["coordinates"]
    elif t in ("LineString", "MultiPoint"):
        yield from geom["coordinates"]
    elif t in ("Polygon", "MultiLineString"):
        for ring in geom["coordinates"]:
            yield from ring
    elif t == "MultiPolygon":
        for poly in geom["coordinates"]:
            for ring in poly:
                yield from ring
    elif t == "GeometryCollection":
        for g in geom["geometries"]:
            yield from coord_stream(g)


def bbox_of(geom):
    pts = list(coord_stream(geom))
    lons, lats = zip(*((p[0], p[1]) for p in pts))
    return [min(lons), min(lats), max(lons), max(lats)]


def ring_area(ring):
    """球面近似前的平面鞋带公式（小范围够用），返回平方度。"""
    return abs(sum(ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1]
                   for i in range(len(ring) - 1))) / 2


print("== FeatureCollection 概览 ==")
print("  feature 数:", len(fc["features"]))
for f in fc["features"]:
    g = f["geometry"]
    print(f"  {f['properties'].get('name', '?'):<8} {g['type']:<12} "
          f"坐标点数={len(list(coord_stream(g)))} bbox={[round(v, 3) for v in bbox_of(g)]}")

print("\n== 整体 bbox ==")
all_pts = [p for f in fc["features"] for p in coord_stream(f["geometry"])]
lons, lats = zip(*((p[0], p[1]) for p in all_pts))
print(f"  [{min(lons):.4f}, {min(lats):.4f}, {max(lons):.4f}, {max(lats):.4f}]")
fc["bbox"] = [min(lons), min(lats), max(lons), max(lats)]

print("\n== Polygon 环校验 ==")
ring = fc["features"][3]["geometry"]["coordinates"][0]
print("  首点:", ring[0], "末点:", ring[-1], "闭合:", ring[0] == ring[-1])
print(f"  鞋带面积（平面近似）: {ring_area(ring):.4f} 平方度")
print("  RFC 7946 建议外环逆时针；本例为顺时针，仅作教学数据")

print("\n== 类型校验 ==")
VALID = {"Point", "MultiPoint", "LineString", "MultiLineString",
         "Polygon", "MultiPolygon", "GeometryCollection"}
def validate_feature(f):
    if f.get("type") != "Feature":
        return "缺少 Feature 类型"
    g = f.get("geometry", {})
    if g.get("type") not in VALID:
        return f"非法几何类型 {g.get('type')}"
    for p in coord_stream(g):
        if not (-180 <= p[0] <= 180 and -90 <= p[1] <= 90):
            return f"坐标越界 {p}"
    return "OK"

for f in fc["features"]:
    print(f"  {f['properties'].get('name', '?'):<8} -> {validate_feature(f)}")

print("\n== 序列化与写盘 ==")
with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp) / "cities.geojson"
    p.write_text(json.dumps(fc, ensure_ascii=False, indent=2), "utf-8")
    loaded = json.loads(p.read_text("utf-8"))
    print(f"  {p.name}: {p.stat().st_size} 字节")
    print("  往返 feature 数一致:", len(loaded["features"]) == len(fc["features"]))
    print("  bbox:", [round(v, 2) for v in loaded["bbox"]])
    # 紧凑格式（生产环境省带宽）
    compact = json.dumps(fc, ensure_ascii=False, separators=(",", ":"))
    print(f"  紧凑格式: {len(compact)} 字符（indent=2 时为 "
          f"{len(json.dumps(fc, ensure_ascii=False, indent=2))} 字符）")

print("\n== properties 查询（属性过滤）==")
big = [f["properties"]["name"] for f in fc["features"]
       if f["properties"].get("pop", 0) > 2200]
print("  人口 > 2200 万:", big)

print("\n== 常见坑 ==")
for line in [
    "坐标顺序是 [lon, lat]，别写成 [lat, lon]",
    "Polygon 外环必须闭合，且不要自相交",
    "WGS84 是默认 CRS；国内数据常是 GCJ-02/BD-09，需先转换",
    "大文件用流式解析（ijson）而非一次性 json.load",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给 FeatureCollection 增加 MultiPolygon（两个不相连区域）并重算 bbox。
# 2. 实现 is_closed(ring) 与 ring_orientation(ring)，判断外环方向。
# 3. 按 bbox 过滤 features，只保留与给定矩形相交的对象。
# 4. 思考：为什么 GeoJSON 规范要规定环的方向？渲染与面积计算会受什么影响？
