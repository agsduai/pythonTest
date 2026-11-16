# ===== 第660课：模板引擎与文本生成-占位符解析与词法扫描 =====
# 知识点：
#   - 模板渲染第一步是「词法扫描」：把模板切成 TEXT / VAR / BLOCK 等 token 流
#   - 手写扫描器用「指针 + 状态」逐字符推进，比正则替换更可控、易扩展
#   - 常见语法：{{ var }} 变量、{% if %} 块、{# comment #} 注释
#   - 转义与原始输出：{{ 内不解释普通文本 }}，遇到 {{ 才进入表达式态
#   - token 用 dataclass 承载（类型、值、位置），报错能定位到第几行第几列
#   - 扫描与渲染分离：token 流可缓存、可单测、可复用于语法高亮
# 依赖：无（标准库）
from dataclasses import dataclass

TEXT, VAR, BLOCK, COMMENT = "TEXT", "VAR", "BLOCK", "COMMENT"


@dataclass
class Token:
    kind: str
    value: str
    line: int
    col: int


def tokenize(source: str) -> list:
    """把模板切成 token 流：{{ }} / {% %} / {# #} 及其余文本。"""
    tokens = []
    i, line, col, n = 0, 1, 1, len(source)
    text_start, text_line, text_col = 0, 1, 1

    def flush_text(end):
        nonlocal text_start, text_line, text_col
        if end > text_start:
            tokens.append(Token(TEXT, source[text_start:end], text_line, text_col))

    while i < n:
        if source.startswith("{{", i) or source.startswith("{%", i) or source.startswith("{#", i):
            flush_text(i)
            opener = source[i:i + 2]
            kind, closer = {"{{": (VAR, "}}"), "{%": (BLOCK, "%}"),
                            "{#": (COMMENT, "#}")}[opener]
            tok_line, tok_col = line, col
            end = source.find(closer, i + 2)
            if end == -1:
                raise ValueError(f"第 {tok_line} 行第 {tok_col} 列：{opener} 未闭合")
            inner = source[i + 2:end].strip()
            tokens.append(Token(kind, inner, tok_line, tok_col))
            consumed = source[i:end + 2]
            line += consumed.count("\n")
            col = len(consumed.rsplit("\n", 1)[-1]) + 1 if "\n" in consumed else col + len(consumed)
            i = end + 2
            text_start, text_line, text_col = i, line, col
        else:
            if source[i] == "\n":
                line += 1
                col = 1
            else:
                col += 1
            i += 1
    flush_text(n)
    return tokens


TPL = """\
你好 {{ name }}！
{# 这是注释，不会输出 #}
{% if vip %}
尊贵的会员，您的积分是 {{ points }}。
{% else %}
普通用户，快去升级吧。
{% endif %}
再见，{{ name }}。
"""

print("== token 流 ==")
toks = tokenize(TPL)
for t in toks:
    value = t.value if t.kind != TEXT else repr(t.value[:36])
    print(f"  L{t.line}:{t.col:<3} {t.kind:<8} {value}")

from collections import Counter
print("\n  统计:", dict(Counter(t.kind for t in toks)))

print("\n== 注释 token 不进入输出 ==")
kept = [t for t in toks if t.kind != COMMENT]
print("  过滤后 token 数:", len(kept), "（注释已丢弃）")

print("\n== 变量插值（只处理 TEXT + VAR）==")
def render_simple(source, ctx):
    out = []
    for t in tokenize(source):
        if t.kind == TEXT:
            out.append(t.value)
        elif t.kind == VAR:
            out.append(str(ctx.get(t.value, f"<{t.value}?>")))
        elif t.kind == BLOCK:
            raise ValueError(f"简单渲染器不支持块: {t.value}")
    return "".join(out)

print(render_simple("你好 {{ name }}，{{ missing }}！", {"name": "小明"}))

print("\n== 未闭合标签报错定位 ==")
for bad in ("{{ name", "{% if x %} 没有 endif", "ok {# 注释没关"):
    try:
        tokenize(bad)
        print(f"  {bad!r}: 通过（若是块错误由解析阶段发现）")
    except ValueError as e:
        print(f"  {bad!r} -> {type(e).__name__}: {e}")

print("\n== 转义与字面量 ==")
# 想输出字面 {{ 时，模板里用 {{ '{{' }} 或定义 escape 规则
print("  {{ 会被识别为变量起始；字面花括号需单独约定转义规则")
print("  常见做法：{{ '{{' }} 或 {{ literal }} 里由渲染器提供")

print("\n== 为什么先扫描再渲染 ==")
for line in (
    "  token 流可缓存：同一模板编译一次，渲染 N 次只跑求值",
    "  语法错误在编译期暴露，不会渲染到一半才崩",
    "  块结构（if/for）需要 token 序列才能配对，正则替换做不到",
    "  词法层不关心变量是否存在，职责单一、易测",
):
    print(line)

# ===== 练习题 =====
# 1. 给 tokenize 增加 {{ var | filter }} 语法，把过滤器名解析进 Token。
# 2. 实现行号/列号精确追踪，验证跨行模板里每个 token 的位置。
# 3. 增加 {% raw %}...{% endraw %} 块，块内内容全部作为 TEXT。
# 4. 思考：为什么「扫描与渲染分离」比边扫描边替换字符串更可维护？
