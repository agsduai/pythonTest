# ===== 第663课：模板引擎与文本生成-模板继承与片段复用 =====
# 知识点：
#   - 继承：子模板用 {% extends "base" %} + {% block name %} 覆盖父模板同名块
#   - 解析顺序：先展开继承链（子 -> 父 -> 祖父），再按「子覆盖父」合并块表
#   - include / 宏（macro）：可复用的片段，带参数，类似函数
#   - 块内 super() 可引用父块内容（追加而非整体替换）
#   - 渲染时先收集所有 block 定义，再渲染父模板骨架，遇到 block 查最终实现
#   - 全部用 dict 模拟模板仓库，无真实文件 IO
# 依赖：无（标准库）
import re
from dataclasses import dataclass, field


@dataclass
class Template:
    name: str
    source: str
    extends: str | None = None
    blocks: dict = field(default_factory=dict)
    body: str = ""


def parse_template(name, source):
    """拆出 extends、blocks 与其余骨架文本。"""
    m = re.search(r"{%\s*extends\s+['\"]?([\w-]+)['\"]?\s*%}", source)
    extends = m.group(1) if m else None
    source = re.sub(r"{%\s*extends\s+.*?%}", "", source, count=1, flags=re.S) if m else source

    blocks, body = {}, []
    pos = 0
    pattern = re.compile(r"{%\s*block\s+(\w+)\s*%}(.*?){%\s*endblock\s*%}", re.S)
    last = 0
    for match in pattern.finditer(source):
        body.append(source[last:match.start()])
        body.append(f"{{{{@block:{match.group(1)}}}}}")   # 占位符
        blocks[match.group(1)] = match.group(2).strip()
        last = match.end()
    body.append(source[last:])
    return Template(name, source, extends, blocks, "".join(body))


class Engine:
    def __init__(self):
        self.templates = {}
        self.macros = {}

    def add(self, name, source):
        self.templates[name] = parse_template(name, source)

    def chain(self, name):
        """返回从子到父的继承链。"""
        out, seen = [], set()
        cur = name
        while cur:
            if cur in seen:
                raise ValueError(f"循环继承: {cur}")
            if cur not in self.templates:
                raise ValueError(f"找不到模板: {cur}")
            seen.add(cur)
            t = self.templates[cur]
            out.append(t)
            cur = t.extends
        return out

    def resolve_blocks(self, name):
        """子模板优先：从父到子依次覆盖，得到最终块表。"""
        blocks = {}
        for t in reversed(self.chain(name)):    # 父 -> 子
            blocks.update(t.blocks)
        return blocks

    def render(self, name, ctx, macros=None):
        macros = macros or {}
        chain = self.chain(name)
        base = chain[-1]                        # 最顶层父模板作为骨架
        blocks = self.resolve_blocks(name)
        return self.expand(base.body, ctx, blocks, macros, set())

    def expand(self, text, ctx, blocks, macros, rendering):
        """递归展开 block 占位符与 include/macro 调用。"""
        def sub_block(m):
            bname = m.group(1)
            if bname in rendering:
                raise ValueError(f"块 {bname} 递归渲染")
            impl = blocks.get(bname, "")
            return self.expand(impl, ctx, blocks, macros, rendering | {bname})

        text = re.sub(r"\{\{@block:(\w+)\}\}", sub_block, text)

        def sub_include(m):
            inc = m.group(1)
            if inc not in self.templates:
                raise ValueError(f"include 找不到: {inc}")
            return self.expand(self.templates[inc].body, ctx, blocks, macros, rendering)

        text = re.sub(r"{%\s*include\s+['\"]?([\w-]+)['\"]?\s*%}", sub_include, text)

        def sub_macro(m):
            mname, argstr = m.group(1), m.group(2)
            if mname not in macros:
                raise ValueError(f"未定义宏: {mname}")
            args = [a.strip().strip("'\"") for a in argstr.split(",")] if argstr.strip() else []
            return macros[mname](*args)

        text = re.sub(r"{%\s*macro\s+(\w+)\(([^)]*)\)\s*%}", sub_macro, text)
        text = re.sub(r"{{\s*(\w+)\s*}}", lambda m: str(ctx.get(m.group(1), "")), text)
        return text


eng = Engine()
eng.add("base", """\
<!doctype html>
<html>
<head><title>{% block title %}默认标题{% endblock %}</title></head>
<body>
{% include "header" %}
<main>{% block content %}（暂无内容）{% endblock %}</main>
{% include "footer" %}
</body>
</html>
""")
eng.add("header", "<header>站点导航 | {{ site }}</header>")
eng.add("footer", "<footer>© 2026 {{ site }}</footer>")
eng.add("page", """\
{% extends "base" %}
{% block title %}{{ page_title }} - {{ site }}{% endblock %}
{% block content %}
<h1>{{ page_title }}</h1>
{% macro badge('VIP') %}
{% endblock %}
""")

print("== 模板仓库 ==")
for name, t in eng.templates.items():
    print(f"  {name:<8} extends={t.extends!s:<8} blocks={list(t.blocks)}")

print("\n== page 的继承链 ==")
print("  ", " -> ".join(t.name for t in eng.chain("page")))

print("\n== 最终块表（子覆盖父）==")
for k, v in eng.resolve_blocks("page").items():
    print(f"  {k}: {v.strip()[:60]!r}")

print("\n== 渲染结果 ==")
ctx = {"site": "Python 教程", "page_title": "模板继承"}
print(eng.render("page", ctx, macros={"badge": lambda v: f"<span>[{'VIP' if v else '普通'}]</span>"}))

print("\n== 直接渲染 base（未被覆盖的块用默认内容）==")
print(eng.render("base", ctx).splitlines()[2].strip())

print("\n== 循环继承检测 ==")
cyc = Engine()
cyc.add("a", '{% extends "b" %}{% block x %}A{% endblock %}')
cyc.add("b", '{% extends "a" %}{% block x %}B{% endblock %}')
try:
    cyc.chain("a")
except ValueError as e:
    print("  ", type(e).__name__, e)

print("\n== super() 追加父块内容（模拟）==")
# 子块里写 {{ super }} 时，由渲染器注入父块渲染结果
child = '{% extends "base" %}{% block content %}子内容 + {{ super }}{% endblock %}'
eng2 = Engine()
eng2.add("base2", "<main>{% block content %}父内容{% endblock %}</main>")
eng2.add("child2", '{% extends "base2" %}{% block content %}子内容 + {{ super }}{% endblock %}')
parent_impl = eng2.templates["base2"].blocks["content"]
merged = eng2.templates["child2"].blocks["content"].replace("{{ super }}", parent_impl)
print("  合并后块内容:", merged)
print("  说明：真实引擎在渲染块时把父块结果绑成 super 变量")

print("\n== 继承 vs include vs macro ==")
for line in (
    "  extends : 整体骨架复用，子只覆盖局部块，一对一",
    "  include : 把一段静态片段嵌进来，一对多，无覆盖关系",
    "  macro   : 带参数的可复用片段，相当于模板里的函数",
    "  三者可组合：base 定义块，header 用 include，列表项用 macro",
):
    print(line)

# ===== 练习题 =====
# 1. 实现真正的 {{ super }}：渲染子块时把父块渲染结果注入上下文。
# 2. 支持多级继承（祖父 -> 父 -> 子），验证块覆盖顺序正确。
# 3. 增加 {% include name with x=1 %}，给被包含片段传局部参数。
# 4. 思考：为什么块表要「父先入、子后覆盖」，而不是反过来？
