# ===== 第649课：数据交换格式与协议设计-序列化性能与体积对比 =====
# 知识点：
#   - 对比维度：编码后体积、序列化/反序列化耗时、可读性、类型保真、跨语言
#   - 文本格式（JSON/CSV/XML）人可读、跨语言好，但体积大、解析慢
#   - 二进制格式（pickle/struct/自研 TLV）紧凑快，但 pickle 仅限 Python 且不安全
#   - pickle 只能在可信数据上用：反序列化会执行任意代码（第38章安全提醒）
#   - 测量用 timeit/perf_counter，多次取中位数，避免单次抖动
#   - 结论依赖数据形态：键多、重复多、数字多，各自最优格式不同
# 依赖：无（标准库）
import csv
import io
import json
import pickle
import statistics
import struct
import time
import xml.etree.ElementTree as ET
from datetime import datetime

ROWS = [
    {"id": i, "name": f"user_{i % 50}", "score": round(i * 0.75, 2),
     "active": i % 3 != 0, "ts": 1731600000 + i}
    for i in range(500)
]


def json_codec():
    return (lambda d: json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode("utf-8"),
            lambda b: json.loads(b.decode("utf-8")))


def csv_codec():
    fields = ["id", "name", "score", "active", "ts"]
    def enc(rows):
        buf = io.StringIO(newline="")
        w = csv.DictWriter(buf, fieldnames=fields)
        w.writeheader(); w.writerows(rows)
        return buf.getvalue().encode("utf-8")
    def dec(b):
        return list(csv.DictReader(io.StringIO(b.decode("utf-8"), newline="")))
    return enc, dec


def xml_codec():
    def enc(rows):
        root = ET.Element("rows")
        for r in rows:
            e = ET.SubElement(root, "row")
            for k, v in r.items():
                e.set(k, str(v))
        return ET.tostring(root, encoding="utf-8")
    def dec(b):
        return [e.attrib for e in ET.fromstring(b)]
    return enc, dec


def pickle_codec():
    return (lambda d: pickle.dumps(d, protocol=pickle.HIGHEST_PROTOCOL),
            lambda b: pickle.loads(b))


def struct_codec():
    """定长二进制：id(4) + score(8) + active(1) + ts(4)，name 用长度前缀。"""
    def enc(rows):
        out = bytearray(struct.pack(">I", len(rows)))
        for r in rows:
            nb = r["name"].encode("utf-8")
            out += struct.pack(">IdB I B", r["id"], r["score"], 1 if r["active"] else 0,
                               r["ts"], len(nb)) + nb
        return bytes(out)
    def dec(b):
        (n,) = struct.unpack_from(">I", b, 0)
        off, res = 4, []
        for _ in range(n):
            rid, score, active, t, nl = struct.unpack_from(">IdBIB", b, off)
            off += struct.calcsize(">IdBIB")
            name = b[off:off + nl].decode("utf-8"); off += nl
            res.append({"id": rid, "name": name, "score": score,
                        "active": bool(active), "ts": t})
        return res
    return enc, dec


CODECS = {
    "JSON": json_codec(),
    "CSV": csv_codec(),
    "XML": xml_codec(),
    "pickle": pickle_codec(),
    "struct/TLV": struct_codec(),
}

print("== 编码后体积（500 行）==")
sizes = {}
for name, (enc, dec) in CODECS.items():
    data = enc(ROWS)
    sizes[name] = len(data)
    print(f"  {name:<12}: {len(data):>7} 字节")

print("\n== 往返正确性 ==")
for name, (enc, dec) in CODECS.items():
    back = dec(enc(ROWS))
    same_rows = len(back) == len(ROWS)
    # CSV/XML 全字符串，比较首行 id 是否还原
    first_id = str(back[0]["id"])
    print(f"  {name:<12}: 行数一致={same_rows}  首行 id={first_id}  "
          f"类型={type(back[0]['id']).__name__}")

print("\n== 序列化 / 反序列化耗时（各 30 次，取中位数 ms）==")
def bench(fn, n=30):
    samples = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - t0) * 1000)
    return statistics.median(samples)

for name, (enc, dec) in CODECS.items():
    blob = enc(ROWS)
    e_ms = bench(lambda: enc(ROWS))
    d_ms = bench(lambda: dec(blob))
    print(f"  {name:<12}: encode={e_ms:>7.3f}ms  decode={d_ms:>7.3f}ms  "
          f"合计={e_ms + d_ms:>7.3f}ms")

print("\n== 相对 JSON 的体积比 ==")
base = sizes["JSON"]
for name, size in sizes.items():
    print(f"  {name:<12}: {size / base:>5.1%}  ({size} / {base})")

print("\n== 计算属性的 JSON（可写 JSON Lines 追加）==")
lines = b"\n".join(json.dumps(r, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                   for r in ROWS)
print(f"  JSON Lines 体积={len(lines)} 字节（比数组略大，但可逐行追加）")

print("\n== 选型结论 ==")
for line in (
    "  对外 API / 配置      -> JSON（可读、跨语言、工具全）",
    "  表格导出 / Excel     -> CSV（体积小、追加友好）",
    "  文档 / 企业 SOAP     -> XML（schema、命名空间）",
    "  内部高频 / 网络包    -> 定长 struct 或 TLV（最省最快）",
    "  Python 进程间缓存    -> pickle 可用，但绝不接受外部输入",
    "  跨语言二进制         -> Protobuf / MessagePack（需第三方库）",
):
    print(line)

print("\n== 测量注意事项 ==")
for line in [
    "  先预热、多次取中位数，别用单次 time.time()",
    "  区分「冷启动导入」与「稳态编码」，本报告只测稳态",
    "  压缩（gzip）会大幅改变体积结论，见第595课",
    "  真实决策还要算上 schema 校验、网络 MTU 与 CPU 预算",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给每种格式加 gzip 压缩后再测体积，重排「最省」名次。
# 2. 把行数从 500 增到 50000，观察各格式耗时是否线性增长。
# 3. 用 array('d') 存纯数值列，对比 JSON 数字数组的体积。
# 4. 思考：为什么「体积最小」不等于「总体最优」？
