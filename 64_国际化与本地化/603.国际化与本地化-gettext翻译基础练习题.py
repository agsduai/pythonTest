# ===== 第603课：国际化与本地化-gettext翻译基础 =====
# 知识点：
#   - i18n（国际化）：把代码里的可译文本抽出来；l10n（本地化）：提供各语言译文
#   - 标准流程：源码 _() -> xgettext 抽 .pot -> 翻译 .po -> msgfmt 编译 .mo
#   - .mo 是二进制查找表；运行时用 gettext.GNUTranslations 加载
#   - 目录约定：locales/<lang>/LC_MESSAGES/<domain>.mo
#   - NullTranslations.gettext 原样返回，可用于「未翻译」兜底
#   - 本课自写 make_mo() 生成最小 .mo，让示例无需外部工具即可运行
# 依赖：无（标准库）
import gettext
import io
import struct


def make_mo(entries: dict) -> bytes:
    """把 {msgid: msgstr} 打包成 GNU .mo 字节流（教学用最小实现）。"""
    items = [(k.encode("utf-8"), v.encode("utf-8")) for k, v in entries.items()]
    n = len(items)
    off_orig = 28
    off_trans = 28 + 8 * n
    data_off = 28 + 16 * n
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


# ---- 构造中文与英文两份翻译表 ----
ZH = {
    "": "Content-Type: text/plain; charset=UTF-8\n",
    "Hello, {name}!": "你好，{name}！",
    "Save": "保存",
    "Cancel": "取消",
    "File not found": "文件未找到",
    "Welcome to the course": "欢迎学习本课程",
}
EN = {
    "": "Content-Type: text/plain; charset=UTF-8\n",
    "Hello, {name}!": "Hello, {name}!",
    "Save": "Save",
    "Cancel": "Cancel",
    "File not found": "File not found",
    "Welcome to the course": "Welcome to the course",
}

translations = {
    "zh_CN": gettext.GNUTranslations(io.BytesIO(make_mo(ZH))),
    "en_US": gettext.GNUTranslations(io.BytesIO(make_mo(EN))),
    "null": gettext.NullTranslations(),
}

messages = ["Save", "Cancel", "File not found", "Welcome to the course", "Hello, {name}!", "Untranslated key"]
print("== 同一份代码，三种语言输出 ==")
for lang, t in translations.items():
    print(f"\n[{lang}]")
    for msg in messages:
        print(f"  {msg:<26} -> {t.gettext(msg)}")

print("\n== 参数化消息（先翻译，再填值）==")
t = translations["zh_CN"]
print(" ", t.gettext("Hello, {name}!").format(name="小明"))

print("\n== 缺译兜底 ==")
print("  gettext 找不到条目时原样返回 msgid：")
print(" ", t.gettext("Untranslated key"))
print(f"  catalog 条目数（含表头）：{len(t._catalog)}")
print("  可用 fallback 串接多份目录：", hasattr(t, "add_fallback"))

print("\n== install() 与 builtins._ ==")
# 真实项目常用 t.install() 把 _ 放进 builtins，模块里就能直接写 _("Save")
# 演示后立刻还原，避免污染全局
import builtins
t.install()
print("  builtins._('Save') =", builtins._("Save"))
del builtins._

print("\n== 目录结构约定 ==")
for line in [
    "locales/zh_CN/LC_MESSAGES/messages.mo",
    "locales/en_US/LC_MESSAGES/messages.mo",
    "gettext.translation('messages', localedir='locales', languages=['zh_CN'])",
]:
    print("  ", line)

# ===== 练习题 =====
# 1. 新增一门语言（如 ja_JP）的翻译表，并输出同样的消息列表。
# 2. 给 messages 目录加一条带 HTML 标签的消息，思考译文中标签该如何保留。
# 3. 用 add_fallback() 实现「专业术语表 + 通用翻译表」两级查找。
# 4. 思考：为什么占位符要用 {name} 这种命名形式，而不是 %s 按位置拼接？
