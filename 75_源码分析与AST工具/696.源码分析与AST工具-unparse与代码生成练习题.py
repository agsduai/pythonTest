# ===== 第696课：源码分析与AST工具-unparse与代码生成 =====
# 知识点：
#   - ast.unparse(node) 把 AST 还原成可编译的源码（Python 3.9+）
#   - 手工构造 AST 比拼字符串安全：自动处理括号、缩进、转义、优先级
#   - 常用构造：ast.Module / FunctionDef / arguments / Assign / Call / Constant / Name
#   - 新建节点没有 lineno，必须 ast.fix_missing_locations(tree) 才能 compile
#   - 用 ast.unparse 做「解析 -> 改写 -> 还原」的往返验证
#   - 局限：注释、空行、原格式都会丢失；需要保真改写用 libCST
# 依赖：无（标准库）
import ast

print("== unparse 基础：解析再还原 ==")
SRC = '''\
def greet(name, times=1):
    for i in range(times):
        print(f"Hi, {name}!")
    return times * 2
'''
tree = ast.parse(SRC)
back = ast.unparse(tree)
print(back)
print("  还原后可重新解析:", isinstance(ast.parse(back), ast.Module))
print("  语义一致（再次 unparse）:", ast.unparse(ast.parse(back)) == back)

print("\n== unparse 会规范化格式 ==")
for src in ("x=1+2*3", "if(x>0):print('yes')", "d = {'a':1,'b':2}",
            "f( 1 , 2 )", "x = [i*2 for i in range(3) if i>0]"):
    print(f"  {src!r:<38} -> {ast.unparse(ast.parse(src))!r}")

print("\n== 注释会丢失 ==")
with_comment = "# 重要注释\nx = 1  # 行尾注释\n"
print("  原:", repr(with_comment))
print("  后:", repr(ast.unparse(ast.parse(with_comment))))
print("  -> 需要保留注释时不能用 ast.unparse（用 libCST/parso）")


def make_function(name, params, body_expr):
    """手工构造一个 def 节点：def name(params): return <body_expr>"""
    args = ast.arguments(
        posonlyargs=[], args=[ast.arg(arg=p) for p in params],
        vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[],
    )
    fn = ast.FunctionDef(
        name=name, args=args, body=[ast.Return(value=body_expr)],
        decorator_list=[], returns=None, type_comment=None,
    )
    return fn


def make_binop(left, op, right):
    return ast.BinOp(left=ast.Constant(left), op=op, right=ast.Constant(right))


print("\n== 手工构造 AST 生成函数 ==")
expr = ast.BinOp(
    left=make_binop(2, ast.Mult(), 3),
    op=ast.Add(),
    right=ast.BinOp(left=ast.Name(id="x", ctx=ast.Load()), op=ast.Pow(),
                    right=ast.Constant(2)),
)
fn = make_function("calc", ["x"], expr)
module = ast.Module(body=[fn], type_ignores=[])
ast.fix_missing_locations(module)
generated = ast.unparse(module)
print("  ", generated)

print("\n== 编译并执行生成的函数 ==")
ns = {}
exec(compile(module, "<generated>", "exec"), ns)
print("  calc(4) =", ns["calc"](4), "（2*3 + 4**2 = 22）")
print("  calc(0) =", ns["calc"](0))

print("\n== 未 fix_missing_locations 会怎样 ==")
bad = ast.Module(body=[make_function("f", [], ast.Constant(1))], type_ignores=[])
try:
    compile(bad, "<bad>", "exec")
    print("  竟然编译通过")
except (TypeError, ValueError) as e:
    print(f"  compile 报错: {type(e).__name__}: {e}")
ast.fix_missing_locations(bad)
print("  补位置后:", ast.unparse(bad))

print("\n== 批量生成：一组 getter ==")
def make_getter(field):
    args = ast.arguments(posonlyargs=[], args=[ast.arg(arg="self")], vararg=None,
                         kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[])
    attr = ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()),
                         attr=field, ctx=ast.Load())
    return ast.FunctionDef(name=f"get_{field}", args=args,
                           body=[ast.Return(value=attr)], decorator_list=[],
                           returns=None, type_comment=None)

cls = ast.ClassDef(name="Record", bases=[], keywords=[],
                   body=[make_getter(f) for f in ("name", "age", "score")],
                   decorator_list=[])
mod2 = ast.Module(body=[cls], type_ignores=[])
ast.fix_missing_locations(mod2)
print(ast.unparse(mod2))

print("\n== 字符串拼接 vs AST 构造 ==")
for line in (
    "  拼字符串: 简单直接，但要自己处理缩进、转义、括号、关键字冲突",
    "  AST 构造: 冗长但结构正确，转义与优先级由 unparse 保证",
    "  生成少量固定模板用拼串，生成结构化代码用 AST",
    "  两者都应把「生成结果」再 compile/unparse 一次做自检",
):
    print(" ", line)

# ===== 练习题 =====
# 1. 构造带默认参数、类型注解与 docstring 的 FunctionDef 并 unparse。
# 2. 用 AST 生成一个 dataclass 的 __init__ 与 __repr__ 方法。
# 3. 实现 roundtrip 检查：unparse(parse(src)) 后再 parse 不应报错。
# 4. 思考：为什么「先构造 AST 再 unparse」比直接拼源码字符串更可靠？
