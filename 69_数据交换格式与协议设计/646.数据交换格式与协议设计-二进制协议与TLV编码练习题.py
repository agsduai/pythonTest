# ===== 第646课：数据交换格式与协议设计-二进制协议与TLV编码 =====
# 知识点：
#   - TLV（Type-Length-Value）：最经典的自描述二进制编码，易于扩展与跳过未知字段
#   - 与固定结构体对比：TLV 可加字段不破坏旧版本，固定 struct 则必须同步升级
#   - 长度字段的边界：必须校验 length <= 剩余字节，否则会造成越界/拒绝服务
#   - 大端序（网络字节序）用于跨主机；变长整数 VarInt 可省空间（本例用定长演示）
#   - 版本号 + 向后兼容：新增 type 用新编号，旧解析器跳过不认识的 type
#   - 用 struct + io.BytesIO 实现编解码，全部内存操作、可往返验证
# 依赖：无（标准库）
import io
import struct

TYPE_INT, TYPE_STR, TYPE_BYTES, TYPE_BOOL, TYPE_LIST = 1, 2, 3, 4, 5
NAMES = {TYPE_INT: "int", TYPE_STR: "str", TYPE_BYTES: "bytes",
         TYPE_BOOL: "bool", TYPE_LIST: "list"}


def encode_value(value) -> bytes:
    """把 Python 值编码成一段带 type 的 value 字节（不含 type 字段本身）。"""
    if isinstance(value, bool):
        return struct.pack(">B", 1 if value else 0)
    if isinstance(value, int):
        return struct.pack(">q", value)
    if isinstance(value, str):
        b = value.encode("utf-8")
        return struct.pack(">I", len(b)) + b
    if isinstance(value, bytes):
        return struct.pack(">I", len(value)) + value
    if isinstance(value, (list, tuple)):
        body = b"".join(encode_tlv(k, v) for k, v in enumerate(value))
        return struct.pack(">I", len(body)) + body
    raise TypeError(f"不支持的类型: {type(value).__name__}")


def type_of(value) -> int:
    if isinstance(value, bool):
        return TYPE_BOOL
    if isinstance(value, int):
        return TYPE_INT
    if isinstance(value, str):
        return TYPE_STR
    if isinstance(value, bytes):
        return TYPE_BYTES
    if isinstance(value, (list, tuple)):
        return TYPE_LIST
    raise TypeError(type(value))


def encode_tlv(tag: int, value) -> bytes:
    """一条记录：tag(1B) + type(1B) + length(4B) + value。"""
    body = encode_value(value)
    return struct.pack(">BB", tag, type_of(value)) + struct.pack(">I", len(body)) + body


def decode_value(t: int, body: bytes):
    if t == TYPE_BOOL:
        return struct.unpack(">B", body)[0] == 1
    if t == TYPE_INT:
        return struct.unpack(">q", body)[0]
    if t in (TYPE_STR, TYPE_BYTES):
        (n,) = struct.unpack(">I", body[:4])
        raw = body[4:4 + n]
        return raw.decode("utf-8") if t == TYPE_STR else raw
    if t == TYPE_LIST:
        (n,) = struct.unpack(">I", body[:4])
        return decode_stream(body[4:4 + n])
    raise ValueError(f"未知 type={t}")


def decode_stream(data: bytes, strict=True):
    """解析一串 TLV，未知 type 默认跳过（向后兼容）。"""
    buf = io.BytesIO(data)
    out = {}
    while True:
        head = buf.read(6)                 # tag(1)+type(1)+length(4)
        if not head:
            break
        if len(head) != 6:
            raise ValueError("头部被截断")
        tag, typ, length = struct.unpack(">BBI", head)
        remaining = len(data) - buf.tell()
        if length > remaining:
            raise ValueError(f"tag={tag} 声明长度 {length} 超过剩余 {remaining} 字节")
        body = buf.read(length)
        if typ not in NAMES:
            print(f"  [跳过未知 type={typ} tag={tag} length={length}]")
            continue
        out[tag] = decode_value(typ, body)
    return out


def encode_message(pairs) -> bytes:
    """整条消息：magic(4s) + version(1B) + TLV 记录流。"""
    body = b"".join(encode_tlv(tag, v) for tag, v in pairs)
    return struct.pack(">4sB", b"PYTL", 1) + body


def decode_message(data: bytes):
    magic, version = struct.unpack_from(">4sB", data, 0)
    if magic != b"PYTL":
        raise ValueError(f"非法 magic: {magic!r}")
    return version, decode_stream(data[5:])


msg = [
    (1, "alice"), (2, 42), (3, True), (4, b"\x00\xff\x10"),
    (5, [10, "nested", False]),
]
wire = encode_message(msg)
print("== 编码结果 ==")
print(f"  总长度: {len(wire)} 字节")
print("  前 24 字节:", wire[:24].hex(" "))
print("  magic/version:", wire[:4], wire[4])

print("\n== 解码往返 ==")
version, decoded = decode_message(wire)
print("  version:", version)
for tag, value in decoded.items():
    print(f"  tag={tag} type={type(value).__name__:<6} value={value!r}")
print("  与原始一致:", [decoded[k] for k, _ in msg] == [v for _, v in msg])

print("\n== 逐条 TLV 结构（tag/type/length）==")
buf = io.BytesIO(wire[5:])
while True:
    head = buf.read(6)
    if not head:
        break
    tag, typ, length = struct.unpack(">BBI", head)
    value_bytes = buf.read(length)     # 读满 length 后指针自然移到下一条头部
    print(f"  tag={tag} type={NAMES.get(typ, '?'):<6} length={length:>2} "
          f"value={value_bytes.hex(' ')[:40]}")

print("\n== 向后兼容：旧解析器遇到新字段 ==")
future = wire + encode_tlv(99, "new-field-from-v2")
v2, dec2 = decode_message(future)
print(f"  v1 能解析 v2 消息: {len(dec2)} 个已知字段（99 号被跳过）")
print("  已知字段值不变:", all(dec2[k] == decoded[k] for k in decoded))

print("\n== 长度校验（防越界）==")
for bad in (
    struct.pack(">4sB", b"PYTL", 1) + struct.pack(">BBI", 1, TYPE_INT, 999),
    struct.pack(">4sB", b"PYTL", 1) + b"\x01\x02",
    b"XXXX\x01",
):
    try:
        decode_message(bad)
        print("  ! 未报错（需检查）")
    except (ValueError, struct.error) as e:
        print(f"  拒绝: {type(e).__name__}: {e}")

print("\n== TLV vs 固定 struct ==")
for line in (
    "  固定 struct: 最省空间、最快；加字段必须双方同步升级",
    "  TLV        : 多 6 字节/字段开销；可跳过未知字段，平滑演进",
    "  Protobuf   : TLV 思想 + schema + VarInt，工业级方案",
    "  选型       : 内部高频用 struct，跨版本/跨团队用 TLV/schema",
):
    print(line)

# ===== 练习题 =====
# 1. 实现 VarInt 编码替换 4 字节 length，比较短字段的体积收益。
# 2. 增加 CRC32 尾部校验（第601课），解码时验证完整性。
# 3. 给 decode_stream 增加 max_depth，防止嵌套 list 造成栈溢出。
# 4. 思考：为什么「跳过未知 type」是二进制协议向后兼容的关键？
