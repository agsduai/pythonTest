# ===== 第626课：地理空间数据处理-综合案例-POI周边分析流水线 =====
# 知识点：
#   - 综合串起本章：坐标校验 -> GeoJSON 载入 -> 网格索引 -> 半径查询 -> 距离/方位 -> 统计报表
#   - 流水线分层：数据层（原始 POI）、索引层（网格）、分析层（查询与聚合）、展示层（报表）
#   - 每个阶段输出可校验的中间结果，出错能定位到具体环节
#   - 用 dataclass 承载 POI，避免裸元组字段含义不清
#   - 报表用纯文本生成，可替换为 CSV / HTML / 图表输出
#   - 全部标准库、临时目录、离线可运行，不依赖 shapely / geopandas
# 依赖：无（标准库）
import json
import math
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

EARTH_R = 6371008.8


@dataclass(frozen=True)
class POI:
    name: str
    category: str
    lon: float
    lat: float
    rating: float = 0.0

    def pos(self):
        return (self.lon, self.lat)

    def validate(self):
        return -180 <= self.lon <= 180 and -90 <= self.lat <= 90 and 0 <= self.rating <= 5


def haversine(a, b):
    lon1, lat1, lon2, lat2 = map(math.radians, (*a, *b))
    h = (math.sin((lat2 - lat1) / 2) ** 2 +
         math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 2 * EARTH_R * math.asin(math.sqrt(h))


def bearing(a, b):
    lon1, lat1, lon2, lat2 = map(math.radians, (*a, *b))
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def compass(deg):
    return ("北", "东北", "东", "东南", "南", "西南", "西", "西北")[round(deg / 45) % 8]


class Grid:
    def __init__(self, cell=0.01):
        self.cell, self.buckets = cell, {}

    def add(self, poi: POI):
        key = (math.floor(poi.lon / self.cell), math.floor(poi.lat / self.cell))
        self.buckets.setdefault(key, []).append(poi)

    def near(self, lon, lat, radius_m):
        # 把半径换算成「度数环数」，宁可多查不漏查
        deg = radius_m / 111000
        rings = max(1, math.ceil(deg / self.cell))
        cx, cy = math.floor(lon / self.cell), math.floor(lat / self.cell)
        for dx in range(-rings, rings + 1):
            for dy in range(-rings, rings + 1):
                for p in self.buckets.get((cx + dx, cy + dy), ()):
                    d = haversine((lon, lat), p.pos())
                    if d <= radius_m:
                        yield p, d


def to_geojson(pois):
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature",
         "properties": {"name": p.name, "category": p.category, "rating": p.rating},
         "geometry": {"type": "Point", "coordinates": [p.lon, p.lat]}}
        for p in pois]}


def from_geojson(doc):
    return [POI(f["properties"]["name"], f["properties"]["category"],
                *f["geometry"]["coordinates"], f["properties"]["rating"])
            for f in doc["features"]]


def analyze(pois, center, radius_m):
    """返回结构化分析结果（纯函数，便于测试）。"""
    grid = Grid()
    for p in pois:
        grid.add(p)
    hits = sorted(grid.near(*center, radius_m), key=lambda x: x[1])
    rows = [
        {"name": p.name, "category": p.category, "rating": p.rating,
         "distance_m": round(d), "bearing": round(bearing(center, p.pos())),
         "direction": compass(bearing(center, p.pos()))}
        for p, d in hits
    ]
    return {
        "center": center, "radius_m": radius_m, "total_pois": len(pois),
        "matched": len(rows),
        "by_category": dict(Counter(r["category"] for r in rows)),
        "avg_rating": round(sum(r["rating"] for r in rows) / len(rows), 2) if rows else 0,
        "nearest": rows[0]["name"] if rows else None,
        "rows": rows,
    }


def render(result) -> str:
    lines = [
        "=" * 62,
        "POI 周边分析报表",
        f"中心点 ({result['center'][0]:.4f}, {result['center'][1]:.4f})  "
        f"半径 {result['radius_m']} m",
        f"库内 POI {result['total_pois']} 个，命中 {result['matched']} 个，"
        f"平均评分 {result['avg_rating']}",
        "-" * 62,
        f"{'名称':<12}{'类别':<8}{'评分':>5}{'距离':>9}{'方位':>10}",
        "-" * 62,
    ]
    for r in result["rows"]:
        lines.append(f"{r['name']:<12}{r['category']:<8}{r['rating']:>5.1f}"
                     f"{r['distance_m']:>8}m{r['direction']:>9} {r['bearing']:>3}°")
    lines += ["-" * 62, "类别分布: " + ", ".join(
        f"{k}×{v}" for k, v in sorted(result["by_category"].items())),
        f"最近: {result['nearest']}", "=" * 62]
    return "\n".join(lines)


RAW = [
    POI("故宫博物院", "景点", 116.397, 39.918, 4.9),
    POI("景山公园", "景点", 116.396, 39.925, 4.6),
    POI("北海公园", "景点", 116.389, 39.928, 4.7),
    POI("王府井书店", "购物", 116.411, 39.914, 4.3),
    POI("全聚德", "餐饮", 116.405, 39.910, 4.2),
    POI("东来顺", "餐饮", 116.413, 39.917, 4.4),
    POI("北京饭店", "酒店", 116.408, 39.909, 4.5),
    POI("协和医院", "医疗", 116.419, 39.912, 4.6),
    POI("国贸商城", "购物", 116.461, 39.909, 4.5),
    POI("中关村", "购物", 116.316, 39.982, 4.1),
]

print("== 阶段 1：数据校验 ==")
bad = [p.name for p in RAW if not p.validate()]
print(f"  载入 {len(RAW)} 个 POI，非法记录: {bad or '无'}")
print("  类别:", dict(Counter(p.category for p in RAW)))

with tempfile.TemporaryDirectory() as tmp:
    print("\n== 阶段 2：GeoJSON 往返 ==")
    path = Path(tmp) / "pois.geojson"
    path.write_text(json.dumps(to_geojson(RAW), ensure_ascii=False), "utf-8")
    loaded = from_geojson(json.loads(path.read_text("utf-8")))
    print(f"  {path.name}: {path.stat().st_size} 字节，还原 {len(loaded)} 个 POI")
    print("  字段一致:", [p.name for p in loaded] == [p.name for p in RAW])

    print("\n== 阶段 3：建索引 ==")
    g = Grid()
    for p in loaded:
        g.add(p)
    print(f"  网格桶数: {len(g.buckets)}，桶内 POI 数: "
          f"{[len(v) for v in g.buckets.values()][:6]} ...")

    for radius in (800, 2000, 5000):
        print(f"\n== 阶段 4+5：中心 (116.400,39.915) 半径 {radius}m 查询与报表 ==")
        result = analyze(loaded, (116.400, 39.915), radius)
        print(render(result))

    print("\n== 阶段 6：纯函数与一致性验证 ==")
    a = analyze(loaded, (116.400, 39.915), 2000)
    b = analyze(loaded, (116.400, 39.915), 2000)
    print("  同输入同输出:", a == b)
    print("  暴力校验命中数:", sum(
        1 for p in loaded if haversine((116.400, 39.915), p.pos()) <= 2000))
    print("  索引命中数:", a["matched"], "（两者应相等）")

print("\n== 流水线分层 ==")
for line in [
    "数据层 POI / GeoJSON：只管结构与校验",
    "索引层 Grid：只管加速，不含业务规则",
    "分析层 analyze：纯函数，输出结构化结果",
    "展示层 render：只负责排版，可换成 CSV/HTML/图表",
    "任一环节可单独替换或单测，互不耦合",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给 analyze 增加「按类别分组取评分最高 1 个」的 top1 字段。
# 2. 实现 render_csv(result) 与 render_html(result)，复用同一份分析结果。
# 3. 用 624 课的 geohash 替换 Grid，对比两种索引的命中数是否一致。
# 4. 思考：为什么把 analyze 写成纯函数，比「查询时直接 print」更好维护？
