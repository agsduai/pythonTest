# ===== 第610课：国际化与本地化-综合案例-多语言本地化报表 =====
# 知识点：
#   - 综合串起本篇章：gettext 翻译 + zoneinfo 时区 + 区域数字/日期格式 + 模板渲染
#   - 数据层与展示层分离：内部只存 UTC 时刻、float 金额、原始 key
#   - 每个「渲染上下文」= 语言 + 区域 + 时区，三者独立配置
#   - 函数保持纯粹：同样的 rows + context 必得同样的文本，便于缓存与单测
#   - 报表模板里只用命名占位符，译文可自由调整语序
#   - 生产环境用 .po/.mo 文件与 Babel 等工具；本课内存构造便于离线运行
# 依赖：无（标准库）
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import gettext
import io
import struct


def make_mo(entries: dict) -> bytes:
    items = [(k.encode("utf-8"), v.encode("utf-8")) for k, v in entries.items()]
    n = len(items)
    off_orig, off_trans, data_off = 28, 28 + 8 * n, 28 + 16 * n
    strings, orig_tbl, trans_tbl = bytearray(), [], []
    for key, value in items:
        orig_tbl.append((len(key), data_off + len(strings)))
        strings += key + b"\x00"
        trans_tbl.append((len(value), data_off + len(strings)))
        strings += value + b"\x00"
    out = bytearray(struct.pack("<7I", 0x950412DE, 0, n, off_orig, off_trans, 0, 0))
    for length, offset in orig_tbl + trans_tbl:
        out += struct.pack("<II", length, offset)
    return bytes(out + strings)


TEXT = {
    "zh_CN": {
        "": "Content-Type: text/plain; charset=UTF-8\n",
        "Sales Report": "销售报表",
        "Generated at {time}": "生成时间：{time}",
        "Product": "产品", "Qty": "数量", "Unit Price": "单价", "Total": "小计",
        "Grand Total": "合计", "Rows: {n}": "共 {n} 行",
        "Report for {region}": "{region} 区域报表",
    },
    "en_US": {
        "": "Content-Type: text/plain; charset=UTF-8\n",
        "Sales Report": "Sales Report",
        "Generated at {time}": "Generated at {time}",
        "Product": "Product", "Qty": "Qty", "Unit Price": "Unit Price", "Total": "Total",
        "Grand Total": "Grand Total", "Rows: {n}": "Rows: {n}",
        "Report for {region}": "Report for {region}",
    },
    "ja_JP": {
        "": "Content-Type: text/plain; charset=UTF-8\n",
        "Sales Report": "売上レポート",
        "Generated at {time}": "作成日時：{time}",
        "Product": "商品", "Qty": "数量", "Unit Price": "単価", "Total": "小計",
        "Grand Total": "合計", "Rows: {n}": "{n} 件",
        "Report for {region}": "{region} 向けレポート",
    },
}

REGION_RULES = {
    "zh_CN": (",", ".", "¥", True, "%Y/%m/%d %H:%M"),
    "en_US": (",", ".", "$", True, "%m/%d/%Y %I:%M %p"),
    "ja_JP": (",", ".", "¥", True, "%Y/%m/%d %H:%M"),
    "de_DE": (".", ",", "€", False, "%d.%m.%Y %H:%M"),
}
CONTEXTS = {
    "zh_CN": ("zh_CN", "zh_CN", "Asia/Shanghai"),
    "en_US": ("en_US", "en_US", "America/New_York"),
    "ja_JP": ("ja_JP", "ja_JP", "Asia/Tokyo"),
    "de_DE": ("en_US", "de_DE", "Europe/Berlin"),
}


def fmt_money(value: float, region: str) -> str:
    group, dec, symbol, prefix, _ = REGION_RULES[region]
    int_part, frac = f"{abs(value):.2f}".split(".")
    parts = []
    while len(int_part) > 3:
        parts.append(int_part[-3:])
        int_part = int_part[:-3]
    parts.append(int_part)
    num = group.join(reversed(parts)) + dec + frac
    sign = "-" if value < 0 else ""
    return sign + (symbol + num if prefix else num + " " + symbol)


def render(rows, instant_utc: datetime, context: str) -> str:
    lang, region, tzname = CONTEXTS[context]
    t = gettext.GNUTranslations(io.BytesIO(make_mo(TEXT[lang])))
    _ = t.gettext
    local_dt = instant_utc.astimezone(ZoneInfo(tzname))
    stamp = local_dt.strftime(REGION_RULES[region][4]) + f" {tzname}"

    lines = [
        "=" * 46,
        _("Report for {region}").format(region=region) + "  |  " + _("Sales Report"),
        _("Generated at {time}").format(time=stamp),
        "-" * 46,
        f"{_('Product'):<14}{_('Qty'):>6}{_('Unit Price'):>14}{_('Total'):>14}",
        "-" * 46,
    ]
    grand = 0.0
    for name, qty, price in rows:
        total = qty * price
        grand += total
        lines.append(f"{name:<14}{qty:>6}{fmt_money(price, region):>14}{fmt_money(total, region):>14}")
    lines += [
        "-" * 46,
        f"{_('Grand Total'):<20}{fmt_money(grand, region):>26}",
        _("Rows: {n}").format(n=len(rows)),
        "=" * 46,
    ]
    return "\n".join(lines)


rows = [
    ("Notebook", 12, 25.5),
    ("Mouse", 40, 8.75),
    ("Keyboard", 7, 49.9),
]
instant = datetime(2026, 11, 14, 1, 30, tzinfo=timezone.utc)

for context in CONTEXTS:
    print(f"\n===== {context} =====")
    print(render(rows, instant, context))

print("\n== 纯函数验证：同输入必得同输出 ==")
a = render(rows, instant, "zh_CN")
b = render(rows, instant, "zh_CN")
print("  两次渲染一致:", a == b)
print("  内部存 UTC，展示才转时区：", instant.isoformat())

print("\n== 上下文三要素可独立组合 ==")
for line in [
    "lang  决定文案与语序（zh_CN / en_US / ja_JP）",
    "region 决定数字、货币与日期形状（可让 en 文案配 de_DE 数字）",
    "tz    决定时间戳显示在哪个时区",
    "de_DE 示例即为「英文文案 + 德国数字格式」的组合",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 增加 fr_FR 上下文（法语文案 + 法国数字格式 + 巴黎时区）。
# 2. 给报表加一列折扣，并在译文里新增对应表头词条。
# 3. 把 render 的结果缓存起来，用 (context, 数据版本号) 作 key，说明失效条件。
# 4. 思考：为什么金额用 Decimal 比 float 更适合财务报表？改动点在哪里？
