# ===== 第605课：国际化与本地化-时区与zoneinfo =====
# 知识点：
#   - naive（无 tzinfo）与 aware（带 tzinfo）：两者不能直接比较或相减
#   - 内部一律存 UTC aware datetime，展示时才转到用户时区
#   - ZoneInfo("Area/City") 读取 IANA 时区库；Windows 需 tzdata 包
#   - astimezone() 转换显示；datetime.now(tz) 取当前时刻
#   - 夏令时 DST：春季有「不存在的 2 点」，秋季有「重复的 1 点」（fold=0/1）
#   - 跨 DST 做「加一天」应加在墙上时间，而不是简单 +timedelta 的绝对时长
# 依赖：无（标准库；Windows 建议 pip install tzdata）
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, available_timezones

UTC = timezone.utc
SH = ZoneInfo("Asia/Shanghai")
NY = ZoneInfo("America/New_York")
LDN = ZoneInfo("Europe/London")

print("== 时区库 ==")
print("  可用时区数:", len(available_timezones()))
print("  Asia/Shanghai:", SH)

print("\n== naive 与 aware ==")
naive = datetime(2026, 11, 14, 9, 0)
aware = datetime(2026, 11, 14, 9, 0, tzinfo=SH)
print("  naive:", naive, "| tzinfo =", naive.tzinfo)
print("  aware:", aware, "| UTC 偏移 =", aware.utcoffset())
print("  转 UTC:", aware.astimezone(UTC))
try:
    _ = aware - naive
except TypeError as e:
    print("  直接相减报错:", type(e).__name__, e)

print("\n== 同一时刻在各地显示 ==")
instant = datetime(2026, 11, 14, 1, 30, tzinfo=UTC)
for tz in (UTC, SH, NY, LDN):
    local = instant.astimezone(tz)
    print(f"  {str(tz):<22} {local:%Y-%m-%d %H:%M %Z}  offset={local.utcoffset()}")

print("\n== 时间戳与往返 ==")
ts = instant.timestamp()
print("  timestamp:", ts)
print("  fromtimestamp(UTC):", datetime.fromtimestamp(ts, UTC))
print("  往返一致:", datetime.fromtimestamp(ts, UTC) == instant)

print("\n== 2026 年纽约夏令时切换 ==")
# 2026-03-08 02:00 跳到 03:00（春天少一小时）；11-01 02:00 退回 01:00（秋天多一小时）
for d in (datetime(2026, 3, 8, 1, 59, tzinfo=NY),
          datetime(2026, 3, 8, 3, 0, tzinfo=NY),
          datetime(2026, 11, 1, 1, 30, tzinfo=NY, fold=0),
          datetime(2026, 11, 1, 1, 30, tzinfo=NY, fold=1)):
    print(f"  {d:%Y-%m-%d %H:%M} fold={d.fold} tz={d.tzname()} utc={d.astimezone(UTC):%H:%M}")

print("\n== 不存在的本地时间（春季跳跃）==")
gap = datetime(2026, 3, 8, 2, 30, tzinfo=NY)
print(f"  {gap:%H:%M} 在纽约并不存在；转 UTC 得 {gap.astimezone(UTC):%H:%M}")
back = gap.astimezone(UTC).astimezone(NY)
print(f"  再转回来变成 {back:%H:%M}（被规范化）")

print("\n== 墙上时间加一天 vs 绝对 24 小时 ==")
start = datetime(2026, 3, 7, 12, 0, tzinfo=NY)
plus_24h = (start.astimezone(UTC) + timedelta(hours=24)).astimezone(NY)
same_wall = start + timedelta(days=1)
print(f"  起点        : {start:%m-%d %H:%M %Z}")
print(f"  绝对 +24h   : {plus_24h:%m-%d %H:%M %Z}（时钟变成 13:00）")
print(f"  墙上 +1 天  : {same_wall:%m-%d %H:%M %Z}（仍是 12:00）")

print("\n== 固定偏移时区（无 DST）==")
plus8 = timezone(timedelta(hours=8))
print("  timezone(+8):", datetime(2026, 6, 1, 12, tzinfo=plus8).utcoffset())
print("  ZoneInfo('Asia/Shanghai') 会按历史规则变化，固定偏移不会")

# ===== 练习题 =====
# 1. 写一个 world_clock(instant, zones) 返回「时区 -> 本地时间字符串」字典。
# 2. 找出 2026 年纽约 DST 开始与结束的 UTC 时刻（提示：逐小时扫描 utcoffset）。
# 3. 把「每天 9:00 提醒」在跨 DST 的一周内展开成 UTC 时刻列表。
# 4. 思考：数据库存 naive UTC 与存 aware UTC，各有什么隐患？
