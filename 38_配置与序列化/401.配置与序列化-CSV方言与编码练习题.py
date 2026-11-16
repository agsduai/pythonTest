# ===== 第401课：配置与序列化-CSV方言与编码 =====
# 知识点：
#   - CSV 不是单一格式：分隔符、引号、换行、编码都可能不同（方言 dialect）
#   - csv.Sniffer 可自动嗅探分隔符；失败时回退到 excel 方言
#   - utf-8-sig：带 BOM 的 UTF-8，Excel 双击打开不乱码
#   - GBK：中文 Windows 的 Excel 常默认按 GBK 读，跨系统要显式指定
#   - newline="" 必须加，否则 Windows 上会出现空行
import csv
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    # ---- 1. 分号分隔 + BOM + 引号包裹 ----
    semi = Path(tmp) / "scores.csv"
    with open(semi, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";", quotechar='"')
        writer.writerow(["姓名", "备注"])
        writer.writerow(["小明", "分号；在引号里也没问题"])
        writer.writerow(["小红", '包含"引号"的文本'])

    first3 = semi.read_bytes()[:3]
    print("BOM 头：", first3, "是 utf-8-sig：", first3 == b"\xef\xbb\xbf")

    # ---- 2. 自动嗅探方言 ----
    with open(semi, newline="", encoding="utf-8-sig") as f:
        sample = f.read(1024)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
            print("嗅探到分隔符：", repr(dialect.delimiter))
        except csv.Error:
            dialect = csv.excel              # 回退
            print("嗅探失败，使用默认 excel 方言")
        rows = list(csv.reader(f, dialect))

    print("读取结果：")
    for row in rows:
        print("  ", row)

    # ---- 3. GBK 编码：模拟中文 Windows Excel ----
    gbk = Path(tmp) / "gbk.csv"
    with open(gbk, "w", newline="", encoding="gbk") as f:
        writer = csv.writer(f)
        writer.writerow(["城市", "人口"])
        writer.writerow(["北京", 2189])
        writer.writerow(["上海", 2487])

    print("\nGBK 文件前 6 字节：", gbk.read_bytes()[:6])
    with open(gbk, newline="", encoding="gbk") as f:
        print("按 GBK 读回：", list(csv.reader(f)))

    # 用错编码读会怎样
    try:
        with open(gbk, newline="", encoding="utf-8") as f:
            f.read()
    except UnicodeDecodeError as exc:
        print("用 UTF-8 读 GBK 报错：", str(exc)[:50], "...")

    # ---- 4. DictWriter：按列名写 ----
    with open(semi, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["姓名", "备注"])
        writer.writerow({"姓名": "小刚", "备注": "追加一行"})

# 选择建议：
#   程序之间交换 → UTF-8（不带 BOM）
#   给 Excel 看   → utf-8-sig；老系统/中文 Excel 可能要求 GBK

# ===== 练习题 =====
# 1. 写一份 tab 分隔（\t）的 CSV，用 Sniffer 验证能识别。
# 2. 读取时用 csv.DictReader，按列名访问“备注”。
# 3. 写函数 to_gbk(src, dst)：把 UTF-8 CSV 转成 GBK（注意异常字符）。
# 4. 思考：为什么 csv 模块要求 open 时加 newline=""？
