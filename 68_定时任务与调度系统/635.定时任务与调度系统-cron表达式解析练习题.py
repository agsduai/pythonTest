# ===== 第635课：定时任务与调度系统-cron表达式解析 =====
# 知识点：
#   - 标准 5 字段 cron：分 时 日 月 周（有些实现加秒/年为 6/7 字段）
#   - 取值：分 0-59、时 0-23、日 1-31、月 1-12、周 0-6（0=周日）
#   - 语法：* 任意、a-b 范围、a,b 列表、*/n 或 a-b/n 步长
#   - 日与周是「或」关系（两者都有限制时命中其一即可），最容易踩坑
#   - 解析成 5 个 set[int]，匹配时逐字段查表，清晰且快
#   - 本课手写解析器，不依赖 croniter；可注入 datetime 做确定性测试
# 依赖：无（标准库）
from datetime import datetime, timedelta

FIELD_SPECS = [
    ("minute", 0, 59), ("hour", 0, 23), ("day", 1, 31),
    ("month", 1, 12), ("weekday", 0, 6),
]
ALIASES = {"SUN": 0, "MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6}
MONTH_ALIASES = {"JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
                 "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12}


def parse_field(expr, low, high, aliases=None):
    """把一个 cron 字段解析成允许值集合。"""
    aliases = aliases or {}
    result = set()
    for part in expr.split(","):
        part = part.upper().strip()
        step = 1
        if "/" in part:
            part, step_s = part.split("/", 1)
            step = int(step_s)
            if step <= 0:
                raise ValueError("步长必须为正整数")
        if part == "*":
            lo, hi = low, high
        elif "-" in part:
            a, b = part.split("-", 1)
            lo, hi = resolve(a, aliases), resolve(b, aliases)
        else:
            lo = hi = resolve(part, aliases)
        if lo < low or hi > high or lo > hi:
            raise ValueError(f"字段 {part!r} 超出范围 {low}~{high}")
        result.update(range(lo, hi + 1, step))
    return result


def resolve(token, aliases):
    token = token.upper()
    if token in aliases:            # 注意：不能写成 aliases.get(token, int(token))，
        return aliases[token]       # 默认值里的 int(token) 会被提前求值
    return int(token)


def parse(expr):
    parts = expr.split()
    if len(parts) != 5:
        raise ValueError(f"cron 需要 5 个字段，实际 {len(parts)}")
    parsed = {}
    for (name, low, high), part in zip(FIELD_SPECS, parts):
        aliases = ALIASES if name == "weekday" else (MONTH_ALIASES if name == "month" else None)
        parsed[name] = parse_field(part, low, high, aliases)
    # 记录日/周是否被写成通配符，用于实现「或」语义
    parsed["day_wild"] = parts[2] == "*"
    parsed["weekday_wild"] = parts[4] == "*"
    return parsed


def matches(cron, dt: datetime) -> bool:
    # Python weekday(): 周一=0 -> cron 周日=0：要 +1 再取模 7
    wd = (dt.weekday() + 1) % 7
    if dt.minute not in cron["minute"] or dt.hour not in cron["hour"]:
        return False
    if dt.month not in cron["month"]:
        return False
    day_hit = dt.day in cron["day"]
    wd_hit = wd in cron["weekday"]
    if cron["day_wild"] and cron["weekday_wild"]:
        return True
    if cron["day_wild"]:
        return wd_hit
    if cron["weekday_wild"]:
        return day_hit
    return day_hit or wd_hit      # 日与周同时限制：或关系


def next_runs(expr, start: datetime, count=5):
    """逐分钟扫描，返回接下来 count 个命中时刻。"""
    cron = parse(expr)
    cur = start.replace(second=0, microsecond=0) + timedelta(minutes=1)
    out = []
    while len(out) < count:
        if matches(cron, cur):
            out.append(cur)
        cur += timedelta(minutes=1)
    return out


print("== 字段解析 ==")
for expr in ("*", "*/15", "1-5", "1,3,5", "10-30/5", "MON-FRI"):
    low, high = (0, 6) if expr == "MON-FRI" else (0, 59)
    aliases = ALIASES if expr == "MON-FRI" else None
    print(f"  {expr:<10} -> {sorted(parse_field(expr, low, high, aliases))}")

print("\n== 完整表达式 ==")
expressions = [
    "* * * * *",
    "0 9 * * 1-5",
    "*/15 9-18 * * *",
    "0 0 1 * *",
    "30 8 * * MON",
    "0 12 1 * 1",       # 日与周同时限制
]
start = datetime(2026, 11, 14, 8, 0)   # 周六
for e in expressions:
    nexts = next_runs(e, start, 3)
    print(f"\n  {e}")
    print("   ", " | ".join(d.strftime("%Y-%m-%d %H:%M %a") for d in nexts))

print("\n== 日与周的「或」语义 ==")
# 2026-11 的 1 号是周日；"0 12 1 * 1" 表示「每月 1 号 或 每周一」
cron = parse("0 12 1 * 1")
for d in (datetime(2026, 11, 1, 12), datetime(2026, 11, 2, 12),
          datetime(2026, 11, 9, 12), datetime(2026, 11, 3, 12)):
    print(f"  {d:%m-%d %a %H:%M} -> {matches(cron, d)}")

print("\n== 非法表达式 ==")
for e in ("60 * * * *", "* * * * * *", "*/0 * * * *", "5-1 * * * *", "* * 32 * *"):
    try:
        parse(e)
        print(f"  {e!r:<16} 竟然通过（需检查）")
    except (ValueError, TypeError) as ex:
        print(f"  {e!r:<16} 拒绝: {type(ex).__name__}: {ex}")

print("\n== 别名与月份 ==")
print("  MON-FRI ->", sorted(parse_field("MON-FRI", 0, 6, ALIASES)))
print("  JAN,MAR ->", sorted(parse_field("JAN,MAR", 1, 12, MONTH_ALIASES)))

print("\n== 工程要点 ==")
for line in [
    "生产环境用 croniter / APScheduler；手写版适合理解语义与单测",
    "逐分钟扫描只用于演示；真实调度器用「下一次触发时间」直接跳跃",
    "时区与 DST 要显式处理（见第605课），别用本地 naive 时间",
    "秒级/年字段是扩展语法，标准 crontab 只有 5 字段",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 支持 6 字段（首字段为秒）与 @daily/@hourly 宏。
# 2. 用二分或「按字段跳跃」实现 next_run，避免逐分钟空转。
# 3. 给 next_runs 增加 end 参数，返回指定时间窗口内的全部触发点。
# 4. 思考：为什么「日与周」是或关系？如果改成与关系会漏掉哪些任务？
