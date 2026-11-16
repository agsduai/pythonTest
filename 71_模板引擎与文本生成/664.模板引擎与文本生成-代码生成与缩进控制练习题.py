# ===== 第664课：模板引擎与文本生成-代码生成与缩进控制 =====
# 知识点：
#   - 代码生成本质是「结构化数据 -> 文本」，模板只是其中一种手段
#   - 缩进必须结构化：用 Indenter 管理层级，别靠字符串里手敲空格
#   - 空白控制：模板里的换行/缩进会渗进输出，需要 dedent / 行过滤规则
#   - textwrap.dedent 去掉多行字符串的公共前导空白；indent 给整块加前缀
#   - 生成的代码要过 py_compile 自检，避免产出语法错误的文件
#   - 可复现性：同样输入 + 固定排序 -> 字节级一致的输出，便于 diff 与缓存
# 依赖：无（标准库）
import py_compile
import tempfile
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

print("== textwrap 基础 ==")
messy = """
    def hello():
        return 1
"""
print("  dedent:", repr(textwrap.dedent(messy)))
print("  indent:", repr(textwrap.indent("a\nb", "  ")))


class Indenter:
    """按层级生成带缩进的代码行。"""

    def __init__(self, unit="    "):
        self.unit = unit
        self.level = 0
        self.lines = []

    def line(self, text=""):
        self.lines.append(self.unit * self.level + text if text else "")
        return self

    def block(self, header):
        self.line(header)
        self.level += 1
        return self

    def end(self):
        self.level = max(0, self.level - 1)
        return self

    def render(self):
        return "\n".join(self.lines).rstrip() + "\n"


def gen_model(fields, class_name="User"):
    """根据字段表生成一个 dataclass 源码。"""
    g = Indenter()
    g.line("from dataclasses import dataclass")
    g.line()
    g.line("@dataclass")
    g.block(f"class {class_name}:")
    for name, typ in fields:
        g.line(f"{name}: {typ}")
    g.line()
    g.block("def as_dict(self):")
    g.line("return {")
    g.level += 1
    for name, _ in fields:
        g.line(f'"{name}": self.{name},')
    g.level -= 1
    g.line("}")
    return g.render()


print("\n== 生成的 dataclass 源码 ==")
fields = [("name", "str"), ("age", "int"), ("active", "bool")]
source = gen_model(fields)
print(source)

print("== 语法自检（py_compile）==")
with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp) / "generated.py"
    p.write_text(source, "utf-8")
    try:
        py_compile.compile(str(p), doraise=True,
                           cfile=str(Path(tmp) / "g.pyc"))
        print("  生成代码编译通过")
    except py_compile.PyCompileError as e:
        print("  生成代码有语法错误:", e)
    ns = {}
    exec(compile(source, str(p), "exec"), ns)
    obj = ns["User"]("小明", 18, True)
    print("  实例化并调用 as_dict:", obj.as_dict())

print("\n== 空白控制：模板换行渗入输出 ==")
tpl = """\
def f():
    {% for line in body %}
    {{ line }}
    {% endfor %}
"""
print("  原始模板（含模板缩进）:")
print(textwrap.indent(tpl, "  "))
# 模拟渲染：模板行自身缩进成为输出的一部分
rendered_lines = []
for line in tpl.splitlines():
    if line.strip().startswith(("{", "%")):
        continue                              # 丢弃纯控制行
    rendered_lines.append(line)
print("  丢弃控制行后:")
print(textwrap.indent("\n".join(rendered_lines), "  "))
print("  可见多余的空行/缩进 -> 真实引擎用 trim_blocks / lstrip_blocks 处理")

print("\n== 可复现性：排序后输出稳定 ==")
schema_a = [("b", "int"), ("a", "str"), ("c", "bool")]
schema_b = [("c", "bool"), ("a", "str"), ("b", "int")]
out1 = gen_model(sorted(schema_a))
out2 = gen_model(sorted(schema_b))
print("  字段顺序不同，排序后生成结果一致:", out1 == out2)
print("  不排序则不一致:", gen_model(schema_a) != gen_model(schema_b))
print("  工程建议：生成前对 dict/set 结果显式 sorted，避免 diff 抖动")

print("\n== 生成文件的头部约定 ==")
HEADER = textwrap.dedent("""\
    # 本文件由 tools/gen_model.py 自动生成，请勿手工修改
    # 源schema版本: v3
""")
print(HEADER, end="")
print("  加头部 + 生成时间戳要谨慎：时间戳会让每次 diff 都变")

print("\n== 常见生成物 ==")
for line in (
    "  ORM 模型 / Pydantic schema / API 客户端 SDK",
    "  配置类、枚举、路由注册表、序列化器",
    "  SQL 迁移脚本、Terraform/K8s YAML（用专门库更安全）",
    "  测试桩、mock 数据、文档表格",
):
    print(line)

print("\n== 工程要点 ==")
for line in [
    " 缩进用层级对象管理，不手拼 '    ' * n 字符串",
    " 生成后必须自检：py_compile / 解析 / 单元测试",
    " 输出稳定可复现：显式排序、不带随机时间戳",
    " 标注「自动生成」，并把生成器纳入版本管理而非只提交产物",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给 gen_model 增加可选 default 值与类型注解的 Optional 生成。
# 2. 实现 trim_blocks / lstrip_blocks 两个空白控制开关。
# 3. 生成一整个模块的多个类，并验证模块导入与字段访问正常。
# 4. 思考：为什么「生成物 + 生成器」都要进版本库，只提交生成物有什么问题？
