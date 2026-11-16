# ===== 第643课：数据交换格式与协议设计-JSON进阶与流式处理 =====
# 知识点：
#   - json.dumps 常用参数：ensure_ascii、indent、separators、sort_keys、default
#   - JSON 只有 6 种类型；datetime / set / Decimal / bytes 需自定义编码器
#   - default= 处理「序列化时」的类型；object_hook / parse_float 处理「反序列化时」
#   - NaN/Infinity 不是合法 JSON（Python 默认却允许），跨语言要用 null 或字符串
#   - 大文件不要一次性 load：JSON Lines（每行一个 JSON）可逐行流式处理
#   - 用 io.StringIO 模拟文件流，内存恒定、可单测
# 依赖：无（标准库）
import io
import json
import math
from datetime import datetime, timezone
from decimal import Decimal

print("== 序列化参数对比 ==")
obj = {"name": "张三", "tags": ["b", "a"], "n": 3, "active": True, "extra": None}
print("  默认       :", json.dumps(obj))
print("  ensure_ascii=False:", json.dumps(obj, ensure_ascii=False))
print("  sort_keys  :", json.dumps(obj, sort_keys=True, ensure_ascii=False))
print("  紧凑       :", json.dumps(obj, separators=(",", ":"), ensure_ascii=False))
print("  缩进       :\n" + json.dumps(obj, indent=2, ensure_ascii=False))

print("\n== 自定义序列化（datetime / Decimal / set）==")
def default(o):
    if isinstance(o, datetime):
        return o.isoformat()
    if isinstance(o, Decimal):
        return str(o)              # 保留精度，不转 float
    if isinstance(o, set):
        return sorted(o)
    raise TypeError(f"不支持的类型: {type(o).__name__}")

payload = {
    "created": datetime(2026, 11, 14, 9, 30, tzinfo=timezone.utc),
    "amount": Decimal("19.99"),
    "roles": {"admin", "editor"},
}
text = json.dumps(payload, default=default, ensure_ascii=False)
print("  ", text)
print("  反序列化:", json.loads(text))

class EnhancedEncoder(json.JSONEncoder):
    def default(self, o):
        try:
            return default(o)
        except TypeError:
            return super().default(o)

print("  JSONEncoder 子类:", json.dumps(payload, cls=EnhancedEncoder, ensure_ascii=False))

print("\n== 反序列化钩子：object_hook / parse_float ==")
raw = '{"amount": 19.99, "at": "2026-11-14T09:30:00+00:00", "n": 3}'
def hook(d):
    if "at" in d:
        d["at"] = datetime.fromisoformat(d["at"])
    return d

parsed = json.loads(raw, object_hook=hook, parse_float=Decimal)
print("  ", {k: (type(v).__name__, str(v)) for k, v in parsed.items()})
print("  Decimal 精确:", parsed["amount"] == Decimal("19.99"))

print("\n== NaN / Infinity 的坑 ==")
bad = {"x": float("nan"), "y": float("inf")}
print("  Python 默认输出:", json.dumps(bad))
print("  allow_nan=False 会抛 ValueError：", end=" ")
try:
    json.dumps(bad, allow_nan=False)
except ValueError as e:
    print(type(e).__name__, e)
print("  安全替代:", json.dumps({"x": None, "y": "Infinity"}))

print("\n== JSON Lines 流式处理 ==")
records = [
    {"id": 1, "event": "login", "ok": True},
    {"id": 2, "event": "pay", "ok": False},
    {"id": 3, "event": "login", "ok": True},
    {"id": 4, "event": "logout", "ok": True},
]
stream = io.StringIO()
for r in records:
    stream.write(json.dumps(r, ensure_ascii=False) + "\n")
stream.seek(0)
print("  文件内容:")
for line in stream:
    print("   ", line.rstrip())
stream.seek(0)
ok_count = sum(1 for line in stream if json.loads(line)["ok"])
print("  流式统计 ok=True 条数:", ok_count, "（逐行读，内存只存一行）")

print("\n== 解析失败与容错（坏行不中断整批）==")
dirty = io.StringIO('{"id":1}\nNOT-JSON\n{"id":2}\n')
good, bad_lines = [], []
for i, line in enumerate(dirty, 1):
    try:
        good.append(json.loads(line))
    except json.JSONDecodeError:
        bad_lines.append(i)
print(f"  成功 {len(good)} 行，坏行位置 {bad_lines}（跳过并告警，而非整批失败）")

print("\n== 大小与性能 ==")
big = [{"i": i, "v": i * 1.5} for i in range(1000)]
compact = json.dumps(big, separators=(",", ":"))
pretty = json.dumps(big, indent=2)
print(f"  1000 条记录: 紧凑={len(compact)} 字符, 缩进={len(pretty)} 字符, "
      f"相差 {len(pretty)/len(compact):.1f} 倍")
print("  生产传输用紧凑格式，日志/调试才用 indent")

# ===== 练习题 =====
# 1. 写一个支持 dataclass 与 Enum 的 default 编码器。
# 2. 实现 parse_int= 钩子，把超大整数转成字符串防止前端精度丢失。
# 3. 用 JSON Lines 增量追加写日志，并实现断点续读（记录 offset）。
# 4. 思考：为什么金额用 Decimal 字符串传输，而不是 JSON number？
