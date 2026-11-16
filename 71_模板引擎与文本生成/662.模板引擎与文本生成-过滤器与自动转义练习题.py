# ===== 第662课：模板引擎与文本生成-过滤器与自动转义 =====
# 知识点：
#   - 过滤器管道：{{ name | upper | truncate(8) }}，AST 里记成 (name, [filter...])
#   - html.escape 防 XSS：< > & " ' 分别转成实体；quote=True 连引号也转
#   - 自动转义：默认对 VAR 输出做转义，|safe 显式声明可信（Markup 模式）
#   - 上下文相关转义：HTML / HTML 属性 / JS / URL 规则不同，不能一套通用
#   - urlencode / quote：URL 参数必须编码，否则 ?a=1&b=2 会被截断注入
#   - 关键原则：默认安全，例外显式；「先拼字符串再整体转义」几乎总是错的
# 依赖：无（标准库）
import html
import re
from urllib.parse import quote, urlencode


class Safe:
    """标记「已安全」的字符串，渲染器遇到它不再二次转义。"""
    def __init__(self, text):
        self.text = text
    def __str__(self):
        return self.text


FILTERS = {
    "upper": lambda v: str(v).upper(),
    "lower": lambda v: str(v).lower(),
    "trim": lambda v: str(v).strip(),
    "length": lambda v: len(v),
    "default": lambda v, d="": v if v not in (None, "") else d,
    "truncate": lambda v, n=10: str(v)[:int(n)] + ("..." if len(str(v)) > int(n) else ""),
    "join": lambda v, sep=", ": sep.join(str(x) for x in v),
    "round": lambda v, n=0: round(float(v), int(n)),
    "escape": lambda v: Safe(html.escape(str(v), quote=True)),
    "safe": lambda v: Safe(str(v)),
    "urlencode": lambda v: quote(str(v), safe=""),
}


def parse_expr(expr):
    """解析 'var | f1 | f2(arg)' -> (变量, [(名, 参数列表)])。"""
    parts = [p.strip() for p in expr.split("|")]
    var, calls = parts[0], []
    for p in parts[1:]:
        m = re.match(r"^(\w+)(?:\((.*)\))?$", p)
        if not m:
            raise ValueError(f"非法过滤器: {p}")
        args = [] if not m.group(2) else [
            a.strip().strip("'\"") for a in m.group(2).split(",")]
        calls.append((m.group(1), args))
    return var, calls


def apply(var, calls, ctx, auto_escape=True):
    value = ctx.get(var)
    marked_safe = False
    for name, args in calls:
        if name not in FILTERS:
            raise ValueError(f"未知过滤器: {name}")
        if name in ("safe", "escape"):
            marked_safe = True
        value = FILTERS[name](value, *args)
    if auto_escape and not marked_safe:
        return html.escape(str(value), quote=True)
    return str(value)


print("== 过滤器管道 ==")
ctx = {"name": "  alice  ", "bio": "这是一段很长的个人简介文本", "tags": ["py", "web", "cli"],
       "score": 3.14159, "empty": "", "html": "<script>alert(1)</script>"}
exprs = [
    "name | trim | upper",
    "bio | truncate(8)",
    "tags | join",
    "tags | join(' + ') | upper",
    "score | round(2)",
    "empty | default(未提供)",
    "name | length",
]
for e in exprs:
    var, calls = parse_expr(e)
    print(f"  {e:<32} -> {apply(var, calls, ctx, auto_escape=False)!r}")

print("\n== 自动转义防 XSS ==")
payload = {"html": "<script>alert('x')</script>", "attr": '" onmouseover="evil()'}
for var in ("html", "attr"):
    out = apply(var, [], {"html": payload["html"], "attr": payload["attr"]})
    print(f"  {var} 默认输出: {out}")
    print(f"    含 <script>: {'<script>' in out}")

print("\n== |safe 与 |escape ==")
print("  |safe   :", apply("html", [("safe", [])], ctx))
print("  |escape :", apply("html", [("escape", [])], ctx))
print("  |escape|upper（先转义再变换）:", end=" ")
var, calls = parse_expr("html | escape | upper")
print(apply(var, calls, ctx))
print("  注意：|safe 只能用于真正可信的内容，滥用等于关闭防护")

print("\n== 上下文相关转义 ==")
def html_text(s): return html.escape(s, quote=False)
def html_attr(s): return html.escape(s, quote=True)
def js_string(s): return s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
def url_param(s): return quote(s, safe="")

s = "a'b\"<&>"
print(f"  原始            : {s}")
print(f"  HTML 文本       : {html_text(s)}")
print(f"  HTML 属性       : {html_attr(s)}")
print(f"  JS 字符串       : {js_string(s)}")
print(f"  URL 参数        : {url_param(s)}")
print("  可见四套规则互不相同，通用 escape 无法覆盖全部场景")

print("\n== URL 编码 ==")
params = {"q": "Python & Django", "page": 2, "tag": "a/b"}
print("  urlencode :", urlencode(params))
print("  quote     :", quote("/搜索?q=中文", safe=""))
print("  反例：'q=' + 用户输入 不编码，& 会截断出额外参数")

print("\n== 错误做法：先拼接再转义 ==")
bad_html = f"<p>{ctx['html']}</p>"
print("  拼接后整体 escape:", html.escape(bad_html))
print("  连自己写的 <p> 都被转义了 -> 结构被破坏")
good_html = "<p>" + html.escape(ctx["html"]) + "</p>"
print("  正确（逐变量转义）:", good_html)

print("\n== 过滤器设计要点 ==")
for line in [
    "  过滤器是纯函数：同输入同输出，可自由组合、可缓存",
    "  auto_escape 默认开启，|safe 是显式例外且要 code review",
    "  输出位置决定转义方式，模板引擎需知道当前上下文",
    "  生产用 markupsafe.Markup + Jinja2 的上下文感知转义",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 增加 |replace(old,new) 与 |pluralize(singular,plural) 过滤器。
# 2. 实现「过滤器参数支持变量引用」而不是只能写字面量。
# 3. 给渲染器增加上下文状态（HTML / JS / URL），自动选择对应转义函数。
# 4. 思考：为什么「先拼好整段 HTML 再 escape」既不安全也不可用？
