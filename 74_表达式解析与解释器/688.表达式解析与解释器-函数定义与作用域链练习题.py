# ===== 第688课：表达式解析与解释器-函数定义与作用域链 =====
# 知识点：
#   - 函数是一等对象：定义时捕获「定义处环境」（闭包），调用时创建调用帧
#   - 作用域链：局部 env -> 父 env -> 全局 env；变量查找逐层向上
#   - 形参绑定：调用时把实参绑到新帧，遮蔽外层同名变量
#   - 递归：每一层调用创建独立帧，天然支持，但要防栈溢出
#   - return 用专用异常从深层执行栈一路跳出，比层层返回标记更干净
#   - 与 Python 真实作用域（LEGB，第33课）对照理解
# 依赖：无（标准库）

print("== 作用域链 Env ==")
class Env:
    def __init__(self, parent=None, values=None):
        self.parent = parent
        self.values = dict(values or {})

    def get(self, name):
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise NameError(f"未定义变量: {name}")

    def set(self, name, value):
        self.values[name] = value      # 只写当前层（遮蔽）

    def chain(self):
        out, cur = [], self
        while cur:
            out.append(dict(cur.values))
            cur = cur.parent
        return out


class ReturnSignal(Exception):
    """解释器里用异常实现 return，可一次穿透多层执行栈。"""
    def __init__(self, value):
        self.value = value


g = Env(values={"x": 1, "pi": 3.14})
f1 = Env(g, {"y": 2, "x": 99})       # 局部 x 遮蔽全局 x
f2 = Env(f1, {"z": 3})
print("  全局:", g.chain())
print("  帧链:", f2.chain())
for name in ("x", "y", "z", "pi"):
    print(f"  f2.get({name!r}) = {f2.get(name)}")
try:
    f2.get("missing")
except NameError as e:
    print("  未定义变量:", e)

print("\n== 递归：每层调用一个独立帧 ==")
global_env = Env(values={"base": 10})

def fact(n, depth=0):
    frame = Env(global_env, {"n": n, "depth": depth})
    if n <= 1:
        return 1, frame
    val, _ = fact(n - 1, depth + 1)
    return n * val, frame

for n in (1, 5, 8):
    val, _ = fact(n)
    print(f"  fact({n}) = {val}")
val, top = fact(4)
print("  最外层帧链长度:", len(top.chain()))
chain_nodes = []
cur = top
while cur:
    chain_nodes.append(cur)
    cur = cur.parent
# 只有调用帧带 n，最底下的 global_env 没有
n_values = [d.values["n"] for d in chain_nodes if "n" in d.values]
print("  各调用帧 n 值:", n_values)
print("  帧链含全局层:", any("base" in d.values for d in chain_nodes))
print("  每层的 n 互不覆盖，这就是调用帧的意义")

print("\n== 闭包：函数捕获定义处环境 ==")
def make_adder(k):
    captured = Env(global_env, {"k": k})
    def adder(x):
        frame = Env(captured, {"x": x})
        return frame.get("x") + frame.get("k")
    return adder

add5 = make_adder(5)
add10 = make_adder(10)
print("  add5(3) =", add5(3), " add10(3) =", add10(3))
print("  两个 adder 各自捕获不同的 k，互不干扰")
print("  若捕获「调用时环境」而非「定义时环境」，结果就会串味")

print("\n== 参数遮蔽外层同名变量 ==")
outer = Env(values={"x": 100})
inner = Env(outer, {"x": 7})
print(f"  外层 x={outer.get('x')}, 内层 x={inner.get('x')}")
inner.set("x", 8)
print(f"  内层赋值后: 外层={outer.get('x')} 内层={inner.get('x')}（互不影响）")

print("\n== return 用异常穿透多层栈 ==")
def deep_execute(stmts, env):
    """模拟解释器执行语句；遇到 ReturnSignal 直接跳回顶层。"""
    for kind, value in stmts:
        if kind == "set":
            env.set(value[0], value[1])
        elif kind == "return":
            raise ReturnSignal(env.get(value))

def run_function(stmts, params):
    frame = Env(global_env, params)
    try:
        deep_execute(stmts, frame)
    except ReturnSignal as r:
        return r.value
    return None

result = run_function([("set", ("tmp", 7)), ("return", "tmp")], {"arg": 1})
print("  run_function 返回:", result)
print("  ReturnSignal 从嵌套执行里一次性带回值，不用层层判断标志位")

print("\n== LEGB 对照（第33课）==")
for line in (
    "  L local    : 当前调用帧",
    "  E enclosing: 闭包 / 外层函数环境",
    "  G global   : 模块级环境",
    "  B builtins : 内置白名单",
    "  本例 Env.chain 就是 L->E->G 的查找链",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  return 用异常穿透多层执行栈，避免层层传递状态标记",
    "  递归深度要设上限，否则栈溢出（Python 默认约 1000）",
    "  闭包持有外部环境引用，注意生命周期与内存占用",
    "  尾递归在 Python 里不优化，深递归改循环",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给第687课解释器加 def 语句，用 Env 链实现真正的函数定义与调用。
# 2. 增加 global / nonlocal 语义，允许写入外层变量而不是遮蔽。
# 3. 实现尾调用优化，把 fact 改写成累加器形式避免栈增长。
# 4. 思考：为什么闭包必须捕获「定义时环境」而不是「调用时环境」？
