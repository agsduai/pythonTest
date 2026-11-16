# ===== 第694课：源码分析与AST工具-NodeTransformer与代码改写 =====
# 知识点：
#   - ast.NodeTransformer：visit_XXX 返回新节点即替换，返回 None 即删除
#   - 返回单个节点 / 节点列表 / 原节点，语义各不相同；删语句必须返回 None
#   - 改写后要用 ast.fix_missing_locations(node) 补齐新节点的行列号
#   - ast.unparse 把 AST 还原成源码（3.9+），用于查看改写结果
#   - compile(tree, filename, "exec") 可直接执行改写后的 AST
#   - 应用：自动插桩、常量替换、废弃 API 迁移、断言剥离、日志注入
# 依赖：无（标准库）
import ast
import operator

SOURCE = '''\
def compute(x, y):
    DEBUG = True
    if DEBUG:
        print("debug:", x)
    result = x * 2 + y
    assert result > 0
    return result
'''


class StripDebug(ast.NodeTransformer):
    """删除所有 print 调用与 assert 语句。"""
    def visit_Expr(self, node):
        self.generic_visit(node)
        if (isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "print"):
            return None                      # 删除整条表达式语句
        return node

    def visit_Assert(self, node):
        return None                           # 删除断言


class RenameNames(ast.NodeTransformer):
    """把指定变量名统一改名（含读与写）。"""
    def __init__(self, mapping):
        self.mapping = mapping
    def visit_Name(self, node):
        self.generic_visit(node)
        node.id = self.mapping.get(node.id, node.id)
        return node


class ConstantFolder(ast.NodeTransformer):
    """折叠纯字面量的 BinOp（如 2 * 3 -> 6）。"""
    OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
           ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
           ast.Pow: operator.pow, ast.Mod: operator.mod}

    def visit_BinOp(self, node):
        self.generic_visit(node)
        if (isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant)
                and isinstance(node.left.value, (int, float))
                and isinstance(node.right.value, (int, float))):
            fn = self.OPS.get(type(node.op))
            if fn:
                try:
                    value = fn(node.left.value, node.right.value)
                    return ast.copy_location(ast.Constant(value), node)
                except (ZeroDivisionError, OverflowError):
                    pass
        return node


class Instrument(ast.NodeTransformer):
    """在每个函数体开头插入一条计数语句。"""
    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        probe = ast.parse(f"_CALLS[{node.name!r}] = _CALLS.get({node.name!r}, 0) + 1").body[0]
        node.body.insert(0, probe)
        return ast.copy_location(node, node)


def transform(source, transformer, *args):
    tree = ast.parse(source)
    new = transformer(*args).visit(tree)
    ast.fix_missing_locations(new)
    return ast.unparse(new)


print("== 原文 ==")
print(SOURCE)

print("== 1) 删除 print 与 assert ==")
stripped = transform(SOURCE, StripDebug)
print(stripped)

print("\n== 2) 变量改名 x->a, result->total ==")
renamed = transform(SOURCE, RenameNames, {"x": "a", "result": "total"})
print(renamed)

print("\n== 3) 常量折叠（x * 2 + y 里的 2 不动，看 3 * 4 的例子）==")
expr_src = "value = 3 * 4 + 5\nother = a * 2\n"
folded = transform(expr_src, ConstantFolder)
print(f"  原: {expr_src.strip()}")
print(f"  后: {folded.strip()}")

print("\n== 4) 插桩：函数入口计数 ==")
inst = transform(SOURCE, Instrument)
print(inst)

print("\n== 执行改写后的代码 ==")
tree = ast.parse(inst)
ast.fix_missing_locations(tree)
ns = {"_CALLS": {}}
exec(compile(tree, "<instrumented>", "exec"), ns)
print("  compute(3, 4) =", ns["compute"](3, 4))
print("  调用计数:", ns["_CALLS"])

print("\n== 改写链：多个 Transformer 依次作用 ==")
tree = ast.parse(SOURCE)
tree = StripDebug().visit(tree)
tree = RenameNames({"x": "left", "y": "right"}).visit(tree)
ast.fix_missing_locations(tree)
chained = ast.unparse(tree)
print(chained)

print("\n== Transformer 返回值语义 ==")
for line in (
    "  返回节点      : 用新节点替换原节点",
    "  返回节点列表  : 一条语句展开成多条（如插入前后置语句）",
    "  返回 None     : 删除该节点（仅对语句/列表元素安全）",
    "  返回原节点    : 不变；记得先 generic_visit 处理子节点",
):
    print(" ", line)

print("\n== 常见坑 ==")
for line in [
    "  新建的节点没有 lineno/col_offset -> 必须 fix_missing_locations",
    "  在 visit_Expr 里返回 None 会删语句；在 visit_Name 里返回 None 会让树缺节点",
    "  ast.unparse 会重排格式，改写后不适合做「保持原样」的补丁",
    "  生产级自动重构（libCST/parso）能保留注释与空白，AST 做不到",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「把 assert 转成 if not ...: raise AssertionError」的 Transformer。
# 2. 给每个函数返回前插入耗时日志（注意 return 可能在多个分支里）。
# 3. 写个 DeprecationTransformer，把 old_api(...) 调用改成 new_api(...)。
# 4. 思考：为什么 ast.unparse 之后注释会丢失？什么场景必须用 libCST？
