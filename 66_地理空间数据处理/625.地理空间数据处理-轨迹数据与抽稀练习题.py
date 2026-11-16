# ===== 第625课：地理空间数据处理-轨迹数据与抽稀 =====
# 知识点：
#   - 轨迹 = 带时间戳的 (lon, lat, t) 序列；GPS 高频采样冗余大
#   - 速度/加速度：用 Haversine 算段距离，除以时间差；异常尖峰多为漂移
#   - Douglas-Peucker：递归保留离首尾连线最远的点，复杂度 O(n²)（可优化）
#   - 垂距限值法（简单抽稀）：逐点判断到前一点的距离是否超阈值，O(n)
#   - 停留点检测：连续一段时间移动距离小于阈值，即视为停留
#   - 抽稀阈值单位要统一（米），别拿「度」当距离用
# 依赖：无（标准库）
import math
from datetime import datetime, timedelta

EARTH_R = 6371008.8


def haversine(a, b):
    lon1, lat1, lon2, lat2 = map(math.radians, (*a[:2], *b[:2]))
    h = (math.sin((lat2 - lat1) / 2) ** 2 +
         math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 2 * EARTH_R * math.asin(math.sqrt(h))


def perp_distance(p, a, b):
    """点 p 到线段 ab 的垂距（米，平面近似）。"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    if dx == dy == 0:
        return haversine(p, a)
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    proj = (a[0] + t * dx, a[1] + t * dy)
    return math.sqrt((p[0] - proj[0]) ** 2 + (p[1] - proj[1]) ** 2) * 111000


def douglas_peucker(points, epsilon_m):
    """Ramer–Douglas–Peucker 抽稀，保留端点。"""
    if len(points) < 3:
        return list(points)
    dmax, idx = 0.0, 0
    for i in range(1, len(points) - 1):
        d = perp_distance(points[i], points[0], points[-1])
        if d > dmax:
            dmax, idx = d, i
    if dmax > epsilon_m:
        left = douglas_peucker(points[:idx + 1], epsilon_m)
        right = douglas_peucker(points[idx:], epsilon_m)
        return left[:-1] + right
    return [points[0], points[-1]]


def radial_simplify(points, min_m):
    """垂距/间距简化：与上一点距离小于阈值就丢掉。"""
    out = [points[0]]
    for p in points[1:]:
        if haversine(out[-1], p) >= min_m:
            out.append(p)
    if out[-1] != points[-1]:
        out.append(points[-1])
    return out


def segment_stats(points):
    """返回每段的 (距离m, 时长s, 速度m/s)。"""
    rows = []
    for a, b in zip(points, points[1:]):
        d = haversine(a, b)
        dt = (b[2] - a[2]).total_seconds()
        rows.append((d, dt, d / dt if dt > 0 else float("inf")))
    return rows


def detect_stays(points, radius_m=50, min_seconds=120):
    """连续小范围移动超过时长即为一个停留。"""
    stays, start, i = [], 0, 1
    while i < len(points):
        if haversine(points[start], points[i]) > radius_m:
            dur = (points[i - 1][2] - points[start][2]).total_seconds()
            if dur >= min_seconds and i - 1 > start:
                stays.append((start, i - 1, dur))
            start = i - 1
        i += 1
    dur = (points[-1][2] - points[start][2]).total_seconds()
    if dur >= min_seconds and len(points) - 1 > start:
        stays.append((start, len(points) - 1, dur))
    return stays


# ---- 构造一条带噪声的轨迹 ----
t0 = datetime(2026, 11, 14, 9, 0, 0)
track = []
lon, lat = 116.397, 39.908
for i in range(40):
    lon += 0.0009
    lat += 0.00035 + (0.00004 if i % 2 else -0.00004)   # 轻微抖动
    track.append((lon, lat, t0 + timedelta(seconds=i * 10)))

print("== 轨迹概览 ==")
print(f"  点数={len(track)} 起点=({track[0][0]:.5f},{track[0][1]:.5f}) "
      f"终点=({track[-1][0]:.5f},{track[-1][1]:.5f})")
print(f"  时长={(track[-1][2] - track[0][2]).total_seconds() / 60:.1f} 分钟")
total = sum(haversine(a, b) for a, b in zip(track, track[1:]))
print(f"  累计路程={total:.0f} m，直线起终点={haversine(track[0], track[-1]):.0f} m")

print("\n== 分段速度统计 ==")
stats = segment_stats(track)
speeds = [v for _, _, v in stats]
print(f"  段数={len(stats)} 平均={sum(speeds)/len(speeds):.2f} m/s "
      f"最大={max(speeds):.2f} m/s 最小={min(speeds):.2f} m/s")
print(f"  折合平均时速≈{sum(speeds)/len(speeds)*3.6:.1f} km/h")
print("  异常尖峰示例：", [(round(d), round(v, 2)) for d, _, v in stats[:4]])

print("\n== Douglas-Peucker 抽稀 ==")
for eps in (5, 20, 50, 100):
    out = douglas_peucker(track, eps)
    print(f"  epsilon={eps:>3}m: {len(track)} -> {len(out)} 点，"
          f"压缩率={len(out)/len(track):.0%}")

print("\n== 间距简化 ==")
for m in (20, 50, 100):
    out = radial_simplify(track, m)
    print(f"  min={m:>3}m: {len(track)} -> {len(out)} 点")

print("\n== 抽稀后的路程误差 ==")
orig_len = total
for eps in (5, 20, 50):
    out = douglas_peucker(track, eps)
    kept_len = sum(haversine(a, b) for a, b in zip(out, out[1:]))
    print(f"  eps={eps:>3}m: 保留路程={kept_len:.0f}m "
          f"相对误差={abs(kept_len - orig_len) / orig_len:.1%}")

print("\n== 停留点检测 ==")
stay_track = []
cur = t0
for i in range(30):
    # 前 10 点几乎不动（停留），后 20 点移动
    step = 0.0 if i < 10 else 0.001
    stay_track.append((116.397 + i * step, 39.908, cur + timedelta(seconds=i * 15)))
stays = detect_stays(stay_track, radius_m=60, min_seconds=120)
print(f"  检测到 {len(stays)} 个停留：")
for s, e, dur in stays:
    print(f"    点 {s}~{e}，时长 {dur / 60:.1f} 分钟，中心 "
          f"({stay_track[s][0]:.5f},{stay_track[s][1]:.5f})")

print("\n== 工程要点 ==")
for line in [
    "抽稀前先做异常点剔除（速度 > 200km/h 的点多为漂移）",
    "跨 180° 经线、隧道丢星、坐标系混用都要单独处理",
    "阈值以「米」为单位；用度会随纬度变化而失真",
    "海量轨迹按时间分片 + 空间索引，避免一次性载入内存",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 speed_filter(points, max_mps)，剔除超速异常点后重新统计路程。
# 2. 把 Douglas-Peucker 改成非递归版本，处理 10 万点轨迹。
# 3. 给停留点计算加「时间加权中心点」，而不是简单取起点。
# 4. 思考：为什么抽稀阈值不能用固定的「经纬度差值」？
