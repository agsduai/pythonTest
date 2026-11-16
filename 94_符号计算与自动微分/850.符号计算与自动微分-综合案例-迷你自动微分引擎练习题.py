# ===== 第850课：符号计算与自动微分-综合案例-迷你自动微分引擎 =====
# 知识点：
#   - 综合串起本章：表达式树 -> 前向/反向自动微分 -> 计算图 -> 多变量梯度
#   - 反向模式 AD（reverse-mode AD）：一次反向传播计算所有输入的梯度
#   - 与第70章数值微分的区别：数值微分是近似（有限差分），AD 是精确的
#   - PyTorch/TensorFlow/JAX 的核心就是这个机制，本课用纯 Python 从零实现
#   - Tape-based（录制前向操作，反向遍历计算梯度）
#   - 应用：最小化函数（梯度下降）、参数优化、灵敏度分析
# 依赖：无（标准库）
import math


class Var:
    """自动微分变量：记录值和反向传播所需信息。"""
    __slots__ = ("value", "grad", "_parents", "_op")

    def __init__(self, value, parents=(), op=""):
        self.value = value
        self.grad = 0.0
        self._parents = parents    # [(parent_var, local_gradient)]
        self._op = op

    def __add__(self, other):
        other = _wrap(other)
        return Var(self.value + other.value, [(self, 1.0), (other, 1.0)], "+")

    def __radd__(self, other):
        return _wrap(other) + self

    def __sub__(self, other):
        other = _wrap(other)
        return Var(self.value - other.value, [(self, 1.0), (other, -1.0)], "-")

    def __rsub__(self, other):
        return _wrap(other) - self

    def __mul__(self, other):
        other = _wrap(other)
        return Var(self.value * other.value, [(self, other.value), (other, self.value)], "*")

    def __rmul__(self, other):
        return _wrap(other) * self

    def __truediv__(self, other):
        other = _wrap(other)
        return Var(self.value / other.value, [(self, 1/other.value), (other, -self.value/other.value**2)], "/")

    def __pow__(self, p):
        return Var(self.value ** p, [(self, p * self.value ** (p-1))], f"**{p}")

    def __neg__(self):
        return Var(-self.value, [(self, -1.0)], "neg")

    def __repr__(self):
        return f"Var({self.value:.6f}, grad={self.grad:.6f})"


def _wrap(x):
    return x if isinstance(x, Var) else Var(x)


def exp(x):
    x = _wrap(x)
    return Var(math.exp(x.value), [(x, math.exp(x.value))], "exp")


def log(x):
    x = _wrap(x)
    if x.value <= 0: raise ValueError("log 定义域为正数")
    return Var(math.log(x.value), [(x, 1/x.value)], "log")


def sin(x):
    x = _wrap(x)
    return Var(math.sin(x.value), [(x, math.cos(x.value))], "sin")


def backward(root):
    """反向传播：从 root 沿计算图反向遍历，累加梯度。"""
    # 拓扑排序
    topo, visited = [], set()
    def topo_sort(node):
        if node in visited: return
        visited.add(node)
        for parent, _ in node._parents:
            topo_sort(parent)
        topo.append(node)
    topo_sort(root)

    # 初始化 root 的梯度为 1
    root.grad = 1.0
    # 反向遍历
    for node in reversed(topo):
        for parent, local_grad in node._parents:
            parent.grad += node.grad * local_grad


def zero_grad(root):
    """重置所有变量的梯度。"""
    visited = set()
    stack = [root]
    while stack:
        node = stack.pop()
        if node in visited: continue
        visited.add(node)
        node.grad = 0.0
        for parent, _ in node._parents:
            stack.append(parent)


# ---- 验证：f(x) = x^2 + 3x + 2, f'(x) = 2x + 3 ----
print("== 单变量自动微分 ==")
x = Var(2.0)
y = x**2 + 3*x + 2
print(f"  f(2) = {y.value}")
backward(y)
print(f"  f'(2) = {x.grad}（解析解 = 2*2+3 = 7）")

# 多次验证
for xv in (0.0, 1.0, 3.0, -2.0):
    x = Var(xv)
    y = x**2 + 3*x + 2
    backward(y)
    analytic = 2*xv + 3
    print(f"  f'({xv}) = {x.grad:.6f}  解析={analytic:.6f}  一致={abs(x.grad-analytic)<1e-10}")

print("\n== 多变量梯度 ==")
# f(x, y) = x^2 * y + sin(x)
x = Var(2.0); y = Var(3.0)
z = x**2 * y + sin(x)
backward(z)
print(f"  f(2, 3) = x^2*y + sin(x) = {z.value:.6f}")
print(f"  ∂f/∂x = 2*x*y + cos(x) = {2 * 2 * 3 + math.cos(2):.6f}")
print(f"  AD ∂f/∂x = {x.grad:.6f}")
print(f"  ∂f/∂y = x^2 = 4.0")
print(f"  AD ∂f/∂y = {y.grad:.6f}")

print("\n== 复合函数：f(x) = exp(x^2 + 1) ==")
x = Var(1.0)
z = exp(x**2 + 1)
backward(z)
print(f"  f(1) = exp(2) = {z.value:.6f}")
print(f"  f'(x) = 2x·exp(x^2+1) = {2*1*math.exp(2):.6f}")
print(f"  AD f'(1) = {x.grad:.6f}")

print("\n== 除法与 log：更多运算验证 ==")
x = Var(2.0)
z = (x**2 - 1) / (x**2 + 1)
backward(z)
print(f"  f(x) = (x^2-1)/(x^2+1), f(2) = {z.value:.6f}")
print(f"  AD f'(2) = {x.grad:.6f}（解析 4x/(x^2+1)^2 = {8 / 25:.6f}）")
x = Var(1.5)
z = log(x**2 + 1)
backward(z)
print(f"  g(x) = log(x^2+1), g(1.5) = {z.value:.6f}")
print(f"  AD g'(1.5) = {x.grad:.6f}（解析 2x/(x^2+1) = {3 / 3.25:.6f}）")

print("\n== 链式法则的传播过程 ==")
x = Var(1.0)
a = x**2           # a = x^2, da/dx = 2x
b = a + 1          # b = a + 1, db/da = 1
c = exp(b)         # c = exp(b), dc/db = exp(b)
backward(c)
print(f"  x={x.value}")
print(f"  a = x^2 = {a.value:.6f}, da/dx = {a.grad:.6f}")
print(f"  b = a+1 = {b.value:.6f}, db/da = {b.grad:.6f}")
print(f"  c = exp(b) = {c.value:.6f}, dc/db = {c.grad:.6f}")
print(f"  最终 dc/dx = {x.grad:.6f}")
print(f"  解析: dc/dx = exp(x^2+1)·2x = {math.exp(2)*2:.6f}")

print("\n== 用 AD 做梯度下降：最小化 f(x) = (x-3)^2 ==")
x = Var(0.0)
lr = 0.1
history = [(x.value, (x.value-3)**2)]
for step in range(50):
    zero_grad(x)
    loss = (x - 3) ** 2
    backward(loss)
    x = Var(x.value - lr * x.grad)       # 梯度下降步
    history.append((x.value, (x.value-3)**2))
print(f"  初始: x={history[0][0]:.4f} loss={history[0][1]:.4f}")
print(f"  50 步后: x={history[-1][0]:.4f} loss={history[-1][1]:.6f}")
print(f"  最优: x=3, loss=0")
for step in (0, 5, 10, 20, 30, 49):
    xv, loss = history[step]
    print(f"    step {step:>2}: x={xv:.4f} loss={loss:.6f}")

print("\n== 前向模式 vs 反向模式 ==")
for line in (
    "  前向模式（dual number）: 一次前向算「一个输入」的导数",
    "  反向模式（本课）       : 一次反向算「所有输入」的梯度",
    "  经验法则: 输入少输出多用前向，输出少输入多用反向",
    "  ML 中通常输入（参数）多输出（loss）少 → 反向模式是标准选择",
):
    print(" ", line)

print("\n== AD vs 数值微分 vs 符号微分 ==")
print(f"  {'方法':<16}{'精度':<12}{'速度':<12}{'内存':<10}{'特点'}")
for row in (("数值微分", "O(h) 近似", "快", "O(1)", "简单但有误差"),
            ("符号微分", "精确", "表达式膨胀", "O(表达式)", "输出可读"),
            ("前向 AD", "精确", "快", "O(1)/次", "适合输入少"),
            ("反向 AD", "精确", "反向遍历", "O(计算图)", "ML 标准")):
    print(f"  {row[0]:<16}{row[1]:<12}{row[2]:<12}{row[3]}")

print("\n== 与 PyTorch 的对照 ==")
for line in [
    "  PyTorch: torch.Tensor 有 .requires_grad 和 .grad 属性",
    "  loss.backward() 就是本课的 backward(root)",
    "  optimizer.zero_grad() 就是本课的 zero_grad(root)",
    "  本课的 Var 类 = PyTorch 的 Tensor（标量版）",
    "  PyTorch 支持向量化运算和 GPU 加速，本课是纯 Python 教学版",
]:
    print("  -", line)

print("\n== 局限与边界 ==")
for line in [
    "  本实现每次 backward 后需要 zero_grad，否则梯度累加",
    "  不支持原地操作（in-place）如 x += 1，这会破坏计算图",
    "  不支持分支（if/else），因为两个分支的梯度都会被计算",
    "  循环和递归需要展开或使用 scan（RNN 的 BPTT 思路）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现二阶导数：对 backward 的结果再做一次 backward（double backward）。
# 2. 用 AD 实现逻辑回归的训练（梯度下降 + sigmoid + cross-entropy）。
# 3. 实现 Jacobian-vector product（JVP）：前向模式的向量化版本。
# 4. 思考：为什么反向模式 AD 需要「拓扑排序」而不能简单地递归？
