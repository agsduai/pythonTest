# ===== 第846课：符号计算与自动微分-反向模式与计算图 =====
# 知识点：
#   - 计算图（computational graph）：把计算录成 DAG —— 节点 = 中间量，边 = 依赖
#   - 反向模式：先前向求值，再按逆拓扑序把梯度「倒着流」回每个输入
#   - 扇出（fan-out）：一个节点被多个下游使用，梯度必须累加而不是覆盖
#   - 一次反向得到所有输入的梯度：ML 参数百万个、loss 只有一个 -> 反向模式胜出
#   - PyTorch autograd 的 tape 机制与本课的 Graph 同构
# 依赖：无（标准库）
import math


class Node:
    """计算图节点。"""
    __slots__ = ("name", "op", "inputs", "value", "grad")

    def __init__(self, name, op, inputs):
        self.name = name
        self.op = op                 # input/add/sub/mul/square/sin/exp
        self.inputs = inputs         # 上游节点名列表
        self.value = None
        self.grad = 0.0


class Graph:
    """迷你计算图：创建顺序即拓扑序（只允许引用已创建的节点）。"""

    def __init__(self):
        self.nodes = {}              # name -> Node（dict 保有插入顺序）

    def _new(self, name, op, inputs):
        if name in self.nodes:
            raise ValueError(f"节点 {name} 已存在")
        for dep in inputs:
            if dep not in self.nodes:
                raise ValueError(f"节点 {name} 引用了不存在的上游 {dep}")
        self.nodes[name] = Node(name, op, list(inputs))
        return name

    def input(self, name, value):
        self._new(name, "input", [])
        self.nodes[name].value = float(value)
        return name

    def add(self, name, a, b):
        return self._new(name, "add", [a, b])

    def sub(self, name, a, b):
        return self._new(name, "sub", [a, b])

    def mul(self, name, a, b):
        return self._new(name, "mul", [a, b])

    def square(self, name, a):
        return self._new(name, "square", [a])

    def sin(self, name, a):
        return self._new(name, "sin", [a])

    def exp(self, name, a):
        return self._new(name, "exp", [a])

    def forward(self):
        """按创建顺序（= 拓扑序）求值。"""
        for node in self.nodes.values():
            node.grad = 0.0
            node.value = self._apply(node)

    def _apply(self, node):
        tag = node.op
        if tag == "input":
            return node.value
        v = [self.nodes[d].value for d in node.inputs]
        if tag == "add":
            return v[0] + v[1]
        if tag == "sub":
            return v[0] - v[1]
        if tag == "mul":
            return v[0] * v[1]
        if tag == "square":
            return v[0] ** 2
        if tag == "sin":
            return math.sin(v[0])
        if tag == "exp":
            return math.exp(v[0])
        raise ValueError(tag)

    def _partials(self, node):
        """局部导数：[(上游名, d node / d 上游)]。"""
        tag = node.op
        if tag == "input":
            return []
        v = [self.nodes[d].value for d in node.inputs]
        if tag == "add":
            return [(node.inputs[0], 1.0), (node.inputs[1], 1.0)]
        if tag == "sub":
            return [(node.inputs[0], 1.0), (node.inputs[1], -1.0)]
        if tag == "mul":
            return [(node.inputs[0], v[1]), (node.inputs[1], v[0])]
        if tag == "square":
            return [(node.inputs[0], 2.0 * v[0])]
        if tag == "sin":
            return [(node.inputs[0], math.cos(v[0]))]
        if tag == "exp":
            return [(node.inputs[0], node.value)]        # d exp(u)/du = exp(u)
        raise ValueError(tag)

    def topo_check(self):
        """校验创建顺序满足拓扑序。"""
        seen = set()
        for node in self.nodes.values():
            for dep in node.inputs:
                if dep not in seen:
                    return False, node.name
            seen.add(node.name)
        return True, ""

    def backward(self, output):
        """逆拓扑序反向传播，返回每条边的梯度贡献（教学追踪）。"""
        if self.nodes[output].value is None:
            raise RuntimeError("请先调用 forward()")
        for node in self.nodes.values():
            node.grad = 0.0
        self.nodes[output].grad = 1.0
        trace = []
        for node in reversed(list(self.nodes.values())):
            if node.grad == 0.0:
                continue               # 不在输出祖先链上，剪枝
            for up, local in self._partials(node):
                contrib = node.grad * local
                self.nodes[up].grad += contrib
                trace.append((node.name, up, contrib))
        return trace

    def backward_overwrite(self, output):
        """错误示范：覆盖而非累加 —— 扇出处会丢梯度。"""
        for node in self.nodes.values():
            node.grad = 0.0
        self.nodes[output].grad = 1.0
        for node in reversed(list(self.nodes.values())):
            for up, local in self._partials(node):
                self.nodes[up].grad = node.grad * local      # 覆盖！


def build_sample_graph(xv=2.0, yv=3.0):
    g = Graph()
    g.input("x", xv)
    g.input("y", yv)
    g.square("x2", "x")            # x2 = x^2
    g.mul("a", "x2", "y")          # a  = x^2 * y
    g.sin("c", "x")                # c  = sin(x)
    z = g.add("z", "a", "c")       # z  = a + c
    return g, z


print("== 构建计算图：z = x^2 * y + sin(x) ==")
g, zout = build_sample_graph()
ok, bad = g.topo_check()
print(f"  拓扑序检查: {ok}"
      + (f"（节点 {bad} 违反）" if not ok else "（每个节点的输入都先于它创建）"))
print("  图结构:")
for node in g.nodes.values():
    deps = ", ".join(node.inputs) if node.inputs else "-"
    print(f"    {node.name} = {node.op}({deps})")

g.forward()
trace = g.backward(zout)
describe = {"x": "x", "y": "y", "x2": "x^2", "a": "x^2*y", "c": "sin(x)", "z": "输出 z"}
print("\n== 前向求值 + 反向梯度 ==")
print(f"  {'节点':<6}{'表达式':<14}{'值':>10}{'梯度':>12}")
for node in g.nodes.values():
    print(f"  {node.name:<6}{describe[node.name]:<14}{node.value:>10.4f}{node.grad:>12.6f}")
print(f"  解析: dz/dx = 2xy + cos(x) = {2 * 2 * 3 + math.cos(2):.6f},  dz/dy = x^2 = 4.0")


def numeric_grad(fn, point, i, h=1e-6):
    p = [float(t) for t in point]
    p[i] += h
    hi = fn(*p)
    p[i] -= 2 * h
    lo = fn(*p)
    return (hi - lo) / (2 * h)


def f_numeric(xv, yv):
    return xv * xv * yv + math.sin(xv)


print("\n== 数值梯度校验 ==")
for i, name in enumerate(("x", "y")):
    ng = numeric_grad(f_numeric, (2.0, 3.0), i)
    print(f"  d {name}: 计算图 = {g.nodes[name].grad:.6f}   数值差分 = {ng:.6f}")

print("\n== 扇出：一个节点被用两次，梯度要累加 ==")
for src, up, contrib in trace:
    if up == "x":
        print(f"    经由 {src} -> x: {contrib:+.6f}")
total = 0.0
for _, up, contrib in trace:
    if up == "x":
        total += contrib
print(f"  合计 dz/dx = {total:.6f}   （x.grad = {g.nodes['x'].grad:.6f}，累加而非覆盖）")

print("\n== 反例：把累加写成覆盖，梯度悄悄丢失 ==")
g2, z2 = build_sample_graph()
g2.forward()
g2.backward_overwrite(z2)
print(f"  正确 x.grad = {g.nodes['x'].grad:.6f}")
print(f"  覆盖 x.grad = {g2.nodes['x'].grad:.6f}   （丢了 sin 项 {math.cos(2):.6f}）")

print("\n== 例 2：线性模型的参数梯度（一次反向得到 w 与 b）==")
w0, b0, x0, t0 = 1.0, 0.0, 2.0, 5.0
g3 = Graph()
w = g3.input("w", w0)
b = g3.input("b", b0)
xi = g3.input("x", x0)
z = g3.add("z", g3.mul("wx", w, xi), b)
d = g3.sub("d", z, g3.input("t", t0))
L = g3.square("L", d)
g3.forward()
g3.backward("L")
print(f"  模型 z = w*x + b, 损失 L = (z-t)^2, 数据 x={x0}, t={t0}")
print(f"  w={w0}, b={b0} -> z={g3.nodes['z'].value}, L={g3.nodes['L'].value}")
print(f"  dL/dw = {g3.nodes['w'].grad}   （解析 2(z-t)x = {2 * (w0 * x0 + b0 - t0) * x0}）")
print(f"  dL/db = {g3.nodes['b'].grad}   （解析 2(z-t)   = {2 * (w0 * x0 + b0 - t0)}）")
lr = 0.05
w1, b1 = w0 - lr * g3.nodes["w"].grad, b0 - lr * g3.nodes["b"].grad
print(f"  一步梯度下降(lr={lr}): w -> {w1}, b -> {b1}")
g4 = Graph()
w = g4.input("w", w1)
b = g4.input("b", b1)
xi = g4.input("x", x0)
z = g4.add("z", g4.mul("wx", w, xi), b)
d = g4.sub("d", z, g4.input("t", t0))
L = g4.square("L", d)
g4.forward()
print(f"  更新后 L = {g4.nodes['L'].value}（原来 {g3.nodes['L'].value}，损失在下降）")

print("\n== 前向 vs 反向：什么时候选谁 ==")
print(f"  {'场景':<26}{'前向模式':<16}{'反向模式'}")
for row in (("输入 2 个、输出 1 个", "2 次前向", "1 次前向 + 1 次反向"),
            ("输入 10^6 个（神经网络）", "10^6 次前向", "1 次前向 + 1 次反向"),
            ("输出多、输入少（JVP）", "1 次前向", "需多次反向"),
            ("内存", "O(1)", "O(计算图，存中间值)")):
    print(f"  {row[0]:<26}{row[1]:<16}{row[2]}")

print("\n== 小结 ==")
for line in (
    "  反向模式 = 前向求值 + 逆拓扑序的链式法则分发",
    "  扇出处必须累加；「覆盖」是最常见的 autograd 实现 bug",
    "  反向需要保存全部中间值（内存换时间）；重算/分块是工程权衡",
    "  847 课用符号导数解方程；850 课把本章整合成完整引擎",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 给 Graph 增加 div 与 powk（常数指数）节点，重算 z = x^3*y + sin(x)/x 的梯度并数值验证。
# 2. 实现 grad_check(g, output, inputs, h=1e-6)：自动对每个输入做数值梯度比对，返回最大相对误差。
# 3. 用计算图搭两层模型 h = tanh(w1*x + b1), y = w2*h + b2, L = (y-t)^2（给 Graph 加 tanh 节点，
#    局部导数 = 1 - h^2），求 dL/dw1 与 dL/db1。
# 4. 思考：为什么反向传播要等下游梯度全部到齐才能继续分发？「边算边传」会错在哪里？
