# ===== 第609课：国际化与本地化-复数规则与语序 =====
# 知识点：
#   - 不同语言复数类别数不同：中文 1 类、英语 2 类、俄语/阿拉伯语 3~6 类
#   - gettext.ngettext(singular, plural, n) 按 .po 头的 Plural-Forms 选形
#   - Plural-Forms: nplurals=N; plural=<C 风格表达式>；索引即 msgstr 里的第 N 个译文
#   - 不能用 `if n == 1` 硬编码，俄语里 21 也用单数形
#   - 语序差异：不要把句子拆成片段拼接，用「整句模板 + 命名占位符」
#   - 命名占位符用 str.format，译文里可任意调整 {who}/{what} 的先后顺序
# 依赖：无（标准库）
import gettext
import io
import struct


def make_mo(entries: dict) -> bytes:
    """生成 GNU .mo：key 可含 \x00 表示 msgid_plural，value 可含 \x00 分隔复数形。"""
    items = [(k.encode("utf-8"), v.encode("utf-8")) for k, v in entries.items()]
    n = len(items)
    off_orig, off_trans, data_off = 28, 28 + 8 * n, 28 + 16 * n
    strings = bytearray()
    orig_tbl, trans_tbl = [], []
    for key, value in items:
        orig_tbl.append((len(key), data_off + len(strings)))
        strings += key + b"\x00"
        trans_tbl.append((len(value), data_off + len(strings)))
        strings += value + b"\x00"
    out = bytearray(struct.pack("<7I", 0x950412DE, 0, n, off_orig, off_trans, 0, 0))
    for length, offset in orig_tbl:
        out += struct.pack("<II", length, offset)
    for length, offset in trans_tbl:
        out += struct.pack("<II", length, offset)
    return bytes(out + strings)


ZH = {
    "": "Content-Type: text/plain; charset=UTF-8\nPlural-Forms: nplurals=1; plural=0;\n",
    "You have {n} message\u0000You have {n} messages": "你有 {n} 条消息",
    "{who} bought {what}": "{who} 购买了 {what}",
}
EN = {
    "": "Content-Type: text/plain; charset=UTF-8\nPlural-Forms: nplurals=2; plural=(n != 1);\n",
    "You have {n} message\u0000You have {n} messages": "You have {n} message\u0000You have {n} messages",
    "{who} bought {what}": "{who} bought {what}",
}
RU = {
    "": ("Content-Type: text/plain; charset=UTF-8\n"
         "Plural-Forms: nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : "
         "n%10>=2 && n%10<=4 && (n%100<12 || n%100>14) ? 1 : 2);\n"),
    "You have {n} message\u0000You have {n} messages":
        "У вас {n} сообщение\u0000У вас {n} сообщения\u0000У вас {n} сообщений",
    "{who} bought {what}": "{who} купил {what}",
}

catalogs = {lang: gettext.GNUTranslations(io.BytesIO(make_mo(d)))
            for lang, d in (("zh_CN", ZH), ("en_US", EN), ("ru_RU", RU))}

print("== ngettext：同一 n 在各语言选不同复数形 ==")
for n in (0, 1, 2, 5, 11, 21, 22, 101, 111):
    row = []
    for lang, t in catalogs.items():
        row.append(t.ngettext("You have {n} message", "You have {n} messages", n).format(n=n))
    print(f"  n={n:<4} | " + " | ".join(f"{s}" for s in row))

print("\n== 用 plural 表达式算类别索引（手写版）==")
def plural_index(n: int, lang: str) -> int:
    if lang == "zh_CN":
        return 0
    if lang == "en_US":
        return 0 if n == 1 else 1
    if lang == "ru_RU":
        if n % 10 == 1 and n % 100 != 11:
            return 0
        if 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
            return 1
        return 2
    raise ValueError(lang)

print(f"  {'n':<6}{'zh':>5}{'en':>5}{'ru':>5}")
for n in (1, 2, 5, 11, 21, 22, 25, 111):
    print(f"  {n:<6}{plural_index(n, 'zh_CN'):>5}{plural_index(n, 'en_US'):>5}{plural_index(n, 'ru_RU'):>5}")

print("\n== 语序：整句模板 + 命名占位符 ==")
JA = {"": "Content-Type: text/plain; charset=UTF-8\n",
      "{who} bought {what}": "{who} が {what} を購入しました"}
ja = gettext.GNUTranslations(io.BytesIO(make_mo(JA)))
for lang, t in (("en_US", catalogs["en_US"]), ("zh_CN", catalogs["zh_CN"]), ("ja_JP", ja)):
    tpl = t.gettext("{who} bought {what}")
    print(f"  {lang}: {tpl.format(who='小明', what='一本书')}")

print("\n== 反例：片段拼接无法适配语序 ==")
print("  '买了' + what + '，' + who  这种拼接在日语里无法调整语序")
print("  数量词也要随语言变化：中文「3 本书」不需要复数词尾")

print("\n== 数字与名词的顺序差异 ==")
for lang, tpl in (("zh_CN", "共 {n} 条"), ("en_US", "{n} items"),
                  ("ja_JP", "{n} 件"), ("de_DE", "{n} Artikel")):
    print(f"  {lang}: {tpl.format(n=3)}")

# ===== 练习题 =====
# 1. 为阿拉伯语补 6 个复数类别的 Plural-Forms（查 CLDR 规则）并用 ngettext 验证。
# 2. 把练习 609 的 plural_index 扩成支持波兰语（nplurals=3）。
# 3. 设计一条含 3 个占位符的消息，给出中/英/日三种语序不同的译文。
# 4. 思考：为什么复数规则应由翻译数据（Plural-Forms）提供，而不是写死在代码里？
