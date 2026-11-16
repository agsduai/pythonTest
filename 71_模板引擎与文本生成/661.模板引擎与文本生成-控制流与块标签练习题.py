# ===== 第661课：模板引擎与文本生成-控制流与块标签 =====
# 知识点：
#   - 块标签 {% if %} / {% for %} / {% end... %} 需要「配对」，用栈解析成 AST
#   - AST 节点：Text / Var / If / For；递归 render 遍历节点树
#   - 表达式只支持受限子集：变量、点号取属性、== / !=、真假判断（不执行任意代码）
#   - for 循环引入局部作用域：loop.index / loop.first / loop.last
#   - 编译期做结构校验（未闭合、end 不匹配），运行期只做求值
#   - 安全原则：模板语言是「受限 DSL」，绝不把 eval 暴露给模板作者
# 依赖：无（标准库）
from dataclasses import dataclass, field

TEXT, VAR, IF, FOR = "text", "var", "if", "for"


@dataclass
class Node:
    kind: str
    value: str = ""
    children: list = field(default_factory=list)
    alt: list = field(default_factory=list)      # if 的 else 分支


def tokenize(source):
    """复用第660课思路：产出 (kind, value) 简化 token。"""
    out, i, n = [], 0, len(source)
    while i < n:
        if source.startswith("{{", i):
            end = source.find("}}", i + 2)
            out.append((VAR, source[i + 2:end].strip())); i = end + 2
        elif source.startswith("{%", i):
            end = source.find("%}", i + 2)
            out.append(("block", source[i + 2:end].strip())); i = end + 2
        elif source.startswith("{#", i):
            end = source.find("#}", i + 2)
            i = end + 2
        else:
            j = i
            while j < n and not source.startswith(("{{", "{%", "{#"), j):
                j += 1
            out.append((TEXT, source[i:j])); i = j
    return out


def parse(source):
    """把 token 流解析成节点树；用栈处理块配对。"""
    root = []
    stack = [("root", root, None)]
    for kind, value in tokenize(source):
        if kind == TEXT:
            stack[-1][1].append(Node(TEXT, value))
            continue
        if kind == VAR:
            stack[-1][1].append(Node(VAR, value))
            continue
        word, _, arg = value.partition(" ")
        if word == "if":
            node = Node(IF, arg.strip())
            stack[-1][1].append(node)
            stack.append(("if", node.children, node))
        elif word == "else":
            parent = stack[-1][2]
            if parent is None or parent.kind != IF:
                raise ValueError("else 必须配对 if")
            stack[-1] = ("else", parent.alt, parent)
        elif word == "for":
            node = Node(FOR, arg.strip())
            stack[-1][1].append(node)
            stack.append(("for", node.children, node))
        elif word in ("endif", "endfor"):
            expected = {"endif": "if", "endfor": "for"}[word]
            # endif 允许当前处于 if 或 else 分支；endfor 只允许 for
            allowed = (expected, "else") if expected == "if" else (expected,)
            if stack[-1][0] not in allowed:
                raise ValueError(f"{word} 与当前块 {stack[-1][0]} 不匹配")
            stack.pop()
        else:
            raise ValueError(f"未知块标签: {word}")
    if len(stack) != 1:
        raise ValueError(f"存在未闭合块: {stack[-1][0]}")
    return root


def lookup(expr, ctx):
    """受限求值：变量、点号属性、== / !=、not、字面量。"""
    expr = expr.strip()
    if "==" in expr:
        a, b = expr.split("==", 1)
        return lookup(a, ctx) == lookup(b, ctx)
    if "!=" in expr:
        a, b = expr.split("!=", 1)
        return lookup(a, ctx) != lookup(b, ctx)
    if expr.startswith("not "):
        return not lookup(expr[4:], ctx)
    if expr.startswith(("'", '"')) and expr.endswith(("'", '"')):
        return expr[1:-1]
    if expr in ("true", "True"):
        return True
    if expr in ("false", "False", "none", "None"):
        return False if expr in ("false", "False") else None
    if expr.isdigit():
        return int(expr)
    val = ctx
    for part in expr.split("."):
        if isinstance(val, dict):
            val = val.get(part)
        else:
            val = getattr(val, part, None)
        if val is None:
            break
    return val


def render(nodes, ctx):
    out = []
    for node in nodes:
        if node.kind == TEXT:
            out.append(node.value)
        elif node.kind == VAR:
            v = lookup(node.value, ctx)
            out.append("" if v is None else str(v))
        elif node.kind == IF:
            out.append(render(node.children if lookup(node.value, ctx) else node.alt, ctx))
        elif node.kind == FOR:
            # {% for item in items %}
            parts = node.value.split()
            if len(parts) != 3 or parts[1] != "in":
                raise ValueError(f"for 语法错误: {node.value}")
            var, seq = parts[0], lookup(parts[2], ctx) or []
            total = len(seq)
            for i, item in enumerate(seq):
                local = dict(ctx)
                local[var] = item
                local["loop"] = {"index": i + 1, "first": i == 0, "last": i == total - 1}
                out.append(render(node.children, local))
    return "".join(out)


def compile_template(source):
    return parse(source)


TPL = """\
订单列表（共 {{ count }} 单）
{% for o in orders %}
{{ loop.index }}. {{ o.name }} - {{ o.amount }} 元{% if loop.last %} （最后一单）{% endif %}
{% endfor %}
{% if vip %}尊贵会员{% else %}普通用户{% endif %}
"""
ctx = {
    "count": 3, "vip": True,
    "orders": [{"name": "键盘", "amount": 199}, {"name": "鼠标", "amount": 89},
               {"name": "显示器", "amount": 1299}],
}

print("== AST 结构 ==")
def dump(nodes, indent=0):
    for n in nodes:
        print("  " + "  " * indent + f"{n.kind.upper():<5} {n.value!r}")
        if n.children: dump(n.children, indent + 1)
        if n.alt:
            print("  " + "  " * (indent + 1) + "ELSE:")
            dump(n.alt, indent + 2)
dump(compile_template(TPL))

print("\n== 渲染结果 ==")
print(render(compile_template(TPL), ctx))

print("\n== vip=False 走 else 分支 ==")
ctx2 = dict(ctx, vip=False)
print(render(compile_template(TPL), ctx2).splitlines()[-1])

print("\n== 编译期结构校验 ==")
for bad in ("{% if x %} 没闭合", "{% for a in xs %} {% endif %}",
            "{% else %}", "{% unknown %}"):
    try:
        compile_template(bad)
        print(f"  {bad!r}: 通过（需检查）")
    except ValueError as e:
        print(f"  {bad!r} -> {type(e).__name__}: {e}")

print("\n== 受限表达式：不执行任意代码 ==")
for expr, expected in (("vip", True), ("count", 3), ("count == 3", True),
                       ("o.name == '键盘'", False)):
    print(f"  {expr!r:<20} -> {lookup(expr, ctx)!r}")
evil = "__import__('os').system('echo hi')"
print(f"  恶意串 {evil[:24]!r}... -> {lookup(evil, ctx)!r}（只当属性名查，返回 None）")

print("\n== 模板安全原则 ==")
for line in [
    "  模板是 DSL：只暴露白名单内的变量/过滤器，不给 eval/exec",
    "  自动 HTML 转义应在渲染层默认开启（第657课 XSS）",
    "  编译期做结构校验，运行期只求值，错误定位清晰",
    "  生产用 Jinja2：沙箱、自动转义、继承、宏，本课是原理版",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 增加 {% set x = expr %} 赋值节点，并支持在后续变量里引用 x。
# 2. 实现嵌套 for 与 {% if %} 组合，验证 loop 作用域不串味。
# 3. 给 lookup 增加 > / < / and / or，做成完整的受限表达式求值器。
# 4. 思考：为什么模板引擎必须自己实现表达式求值，而不能直接 eval？
