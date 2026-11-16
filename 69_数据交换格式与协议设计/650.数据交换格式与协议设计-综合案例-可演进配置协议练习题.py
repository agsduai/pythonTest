# ===== 第650课：数据交换格式与协议设计-综合案例-可演进配置协议 =====
# 知识点：
#   - 综合串起本章：格式对比 -> Schema 校验 -> 版本迁移 -> 二进制打包 -> 完整性校验
#   - 一条「配置消息」的完整生命周期：编写(v1) -> 校验 -> 迁移(v3) -> 编码 -> 签名 -> 解码 -> 还原
#   - 分层：Schema（约束）/ Migration（演进）/ Codec（表示）/ Integrity（防篡改）
#   - 签名用 hmac-sha256 加在消息尾部；解码先验签再解析（第601课）
#   - 每种格式可插拔：同一个 dict 能导出 JSON / TOML 风格文本 / TLV 二进制
#   - 全部标准库 + 内存/临时目录，离线可运行
# 依赖：无（标准库）
import hashlib
import hmac
import json
import struct
import tempfile
import zlib
from copy import deepcopy
from pathlib import Path

SECRET = b"config-service-secret"
MAGIC = b"CFG1"

V3_SCHEMA = {
    "version": {"type": int, "required": True, "min": 1},
    "service": {"type": str, "required": True, "min_len": 2},
    "port": {"type": int, "required": True, "min": 1, "max": 65535},
    "timeout_ms": {"type": int, "required": False, "default": 3000},
    "features": {"type": list, "required": False, "default": []},
    "labels": {"type": dict, "required": False, "default": {}},
}
MISSING = object()


def validate(data):
    """按 V3_SCHEMA 校验并补默认值，返回 (errors, cleaned)。"""
    errors, cleaned = [], {}
    for field, rule in V3_SCHEMA.items():
        raw = data.get(field, MISSING)
        if raw is MISSING:
            if rule.get("required"):
                errors.append(f"{field}: 缺少必填")
            else:
                cleaned[field] = rule["default"]() if callable(rule["default"]) else rule["default"]
            continue
        if type(raw) is not rule["type"]:
            errors.append(f"{field}: 类型应为 {rule['type'].__name__}，实际 {type(raw).__name__}")
            continue
        if "min" in rule and raw < rule["min"]:
            errors.append(f"{field}: 小于最小值 {rule['min']}")
        if "max" in rule and raw > rule["max"]:
            errors.append(f"{field}: 超过最大值 {rule['max']}")
        if "min_len" in rule and len(raw) < rule["min_len"]:
            errors.append(f"{field}: 长度不足 {rule['min_len']}")
        cleaned[field] = raw
    return errors, cleaned


def migrate(payload):
    """把任意历史版本逐级升级到 v3。"""
    d = deepcopy(payload)
    v = d.get("version", 1)
    if v == 1:
        d.setdefault("timeout_ms", 3000)
        d.setdefault("features", [])
        d["version"] = 2
        v = 2
    if v == 2:
        d.setdefault("labels", {})
        d.setdefault("features", [])
        d["version"] = 3
    return d


def to_json(cfg):
    return json.dumps(cfg, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def to_toml_like(cfg):
    lines = [f'version = {cfg["version"]}', f'service = "{cfg["service"]}"',
             f'port = {cfg["port"]}', f'timeout_ms = {cfg["timeout_ms"]}',
             "features = [" + ", ".join(f'"{x}"' for x in cfg["features"]) + "]",
             "", "[labels]"]
    lines += [f'{k} = "{v}"' for k, v in cfg["labels"].items()]
    return "\n".join(lines).encode("utf-8")


TYPE_MAP = {int: 1, str: 2, list: 3, dict: 4, bool: 5}

def to_tlv(cfg):
    """二进制 TLV：tag 按字段名映射的稳定编号。"""
    tags = {"version": 1, "service": 2, "port": 3, "timeout_ms": 4,
            "features": 5, "labels": 6}
    out = bytearray()
    for key, tag in tags.items():
        val = cfg[key]
        typ = TYPE_MAP.get(type(val))
        if typ is None:
            raise TypeError(key)
        body = json.dumps(val, ensure_ascii=False).encode("utf-8")
        out += struct.pack(">BBI", tag, typ, len(body)) + body
    return bytes(out)


def from_tlv(blob):
    inverse = {"version": 1, "service": 2, "port": 3, "timeout_ms": 4,
               "features": 5, "labels": 6}
    tag2key = {v: k for k, v in inverse.items()}
    out, off = {}, 0
    while off < len(blob):
        tag, typ, length = struct.unpack_from(">BBI", blob, off)
        off += 6
        if length > len(blob) - off:
            raise ValueError("TLV 长度越界")
        out[tag2key.get(tag, f"unknown_{tag}")] = json.loads(blob[off:off + length])
        off += length
    return out


def pack(cfg, fmt="tlv"):
    """完整消息：magic + fmt(1B) + body + crc32(4B) + hmac(32B)。"""
    enc = {"json": to_json, "toml": to_toml_like, "tlv": to_tlv}[fmt]
    body = enc(cfg)
    head = MAGIC + bytes([{"json": 1, "toml": 2, "tlv": 3}[fmt]])
    crc = struct.pack(">I", zlib.crc32(body))
    tag = hmac.new(SECRET, head + body + crc, hashlib.sha256).digest()
    return head + body + crc + tag


def unpack(wire):
    """先验签、再验 CRC、最后解析 —— 顺序不能反。"""
    if wire[:4] != MAGIC:
        raise ValueError("非法 magic")
    fmt_code = wire[4]
    tail = wire[:-36]
    crc_stored = wire[-36:-32]
    tag = wire[-32:]
    expected = hmac.new(SECRET, tail + crc_stored, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected):
        raise ValueError("HMAC 校验失败：数据被篡改或密钥不对")
    body = wire[5:-36]
    if zlib.crc32(body) != struct.unpack(">I", crc_stored)[0]:
        raise ValueError("CRC 校验失败：数据损坏")
    fmt = {1: "json", 2: "toml", 3: "tlv"}[fmt_code]
    if fmt == "json":
        cfg = json.loads(body)
    elif fmt == "tlv":
        cfg = from_tlv(body)
    else:
        raise ValueError("TOML 文本仅作导出展示，回读请用 tomllib（本例不演示）")
    return fmt, cfg


print("== 1) 历史 v1 配置 -> 迁移 -> 校验 ==")
v1_payload = {"service": "billing", "port": 8080, "features": ["retry"]}
migrated = migrate(v1_payload)
errs, cfg = validate(migrated)
print("  v1:", v1_payload)
print("  v3:", cfg)
print("  校验:", errs or "通过")

print("\n== 2) 校验能拦住非法配置 ==")
for bad in ({"version": 3, "service": "x", "port": 0},
            {"version": 3, "service": "ok", "port": 70000},
            {"version": 3, "service": "ok", "port": "8080"}):
    print(f"  {bad} -> {validate(bad)[0]}")

print("\n== 3) 同一份配置的三种表示 ==")
for fmt in ("json", "toml", "tlv"):
    wire = pack(cfg, fmt)
    print(f"  {fmt:<5}: {len(wire):>4} 字节  前 16 字节={wire[:16].hex(' ')}")

print("\n== 4) 编解码往返 ==")
for fmt in ("json", "tlv"):
    wire = pack(cfg, fmt)
    got_fmt, got_cfg = unpack(wire)
    print(f"  {fmt}: 格式={got_fmt} 一致={got_cfg == cfg}")
    print("   ", got_cfg)

print("\n== 5) 完整性：篡改与损坏 ==")
wire = pack(cfg, "tlv")
tampered = bytearray(wire); tampered[10] ^= 0x01
for label, data in (("改 1 字节", bytes(tampered)), ("截断", wire[:-5]), ("原始", wire)):
    try:
        f, c = unpack(data)
        print(f"  {label:<10} -> 解析成功 ({f})")
    except (ValueError, KeyError, struct.error) as e:
        print(f"  {label:<10} -> 拒绝: {type(e).__name__}: {e}")

print("\n== 6) 落盘与重载 ==")
with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp) / "config.bin"
    p.write_bytes(pack(cfg, "tlv"))
    f, c = unpack(p.read_bytes())
    print(f"  {p.name} {p.stat().st_size} 字节 -> {f} 一致={c == cfg}")
    # 同时导出人类可读版本便于 review
    txt = Path(tmp) / "config.toml"
    txt.write_bytes(to_toml_like(cfg))
    print(f"  {txt.name}:\n" + "\n".join("    " + l for l in
          txt.read_text("utf-8").splitlines()))

print("\n== 分层回顾 ==")
for line in [
    "Schema    : 约束类型/范围/必填，补默认值（第647课）",
    "Migration : v1->v2->v3 逐级演进，兼容历史消息（第648课）",
    "Codec     : JSON / TOML 风格 / TLV 可插拔（第643/645/646/649课）",
    "Integrity : CRC 查损坏 + HMAC 防篡改，先验签再解析（第601课）",
    "顺序原则  : 不信任的输入，先验签验完整性，再谈解析与业务",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 toml 回读（用 tomllib），让三种格式都能完整往返。
# 2. 增加密钥轮换：pack 带 key_id，unpack 按 key_id 选密钥。
# 3. 给 TLV 增加「未知字段跳过」，验证 v4 消息能被 v3 解析器安全读取。
# 4. 思考：为什么必须先验 HMAC 再解析 JSON，而不是反过来？
