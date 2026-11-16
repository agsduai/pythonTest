# ===== 第641课：定时任务与调度系统-依赖编排与DAG =====
# 知识点：
#   - 任务间有依赖：抽取 -> 清洗 -> 聚合 -> 报表，天然是有向无环图 DAG
#   - 拓扑排序（Kahn）：反复取入度为 0 的节点；若剩余节点则存在环
#   - 分层执行：同一层的任务互不依赖，可并行；层与层之间必须串行
#   - 失败传播：上游失败时下游标记 SKIPPED，而不是继续跑出脏数据
#   - 环检测要在「注册依赖」时就做，别等运行到一半才发现
#   - 本课纯内存 + 虚拟执行，不引入 Airflow / Prefect 等框架
# 依赖：无（标准库）
from collections import defaultdict, deque
from dataclasses import dataclass, field


@dataclass
class Node:
    name: str
    deps: list = field(default_factory=list)
    state: str = "PENDING"
    duration: float = 1.0


class DAG:
    def __init__(self):
        self.nodes = {}
        self.children = defaultdict(list)

    def add(self, name, deps=(), duration=1.0):
        if name in self.nodes:
            raise ValueError(f"重复任务: {name}")
        self.nodes[name] = Node(name, list(deps), duration=duration)
        for d in deps:
            self.children[d].append(name)

    def validate(self):
        """返回错误信息列表：缺失依赖 + 环。"""
        errors = []
        for name, node in self.nodes.items():
            for d in node.deps:
                if d not in self.nodes:
                    errors.append(f"{name} 依赖不存在的 {d}")
        if errors:
            return errors
        indeg = {n: len(node.deps) for n, node in self.nodes.items()}
        q = deque(n for n, d in indeg.items() if d == 0)
        seen = 0
        while q:
            cur = q.popleft()
            seen += 1
            for child in self.children[cur]:
                indeg[child] -= 1
                if indeg[child] == 0:
                    q.append(child)
        if seen != len(self.nodes):
            errors.append("检测到环，无法拓扑排序")
        return errors

    def layers(self):
        """返回可并行的分层列表。"""
        indeg = {n: len(node.deps) for n, node in self.nodes.items()}
        out, remaining = [], set(self.nodes)
        while remaining:
            ready = sorted(n for n in remaining if indeg[n] == 0)
            if not ready:
                raise RuntimeError("存在环")
            out.append(ready)
            for n in ready:
                remaining.remove(n)
                for c in self.children[n]:
                    indeg[c] -= 1
        return out

    def run(self, fail=()):
        """虚拟执行：fail 中的任务抛错，其下游全部 SKIPPED。"""
        log = []
        for layer in self.layers():
            for name in layer:
                node = self.nodes[name]
                if any(self.nodes[d].state in ("FAILED", "SKIPPED") for d in node.deps):
                    node.state = "SKIPPED"
                    log.append(f"  SKIP    {name:<12} 上游未成功")
                elif name in fail:
                    node.state = "FAILED"
                    log.append(f"  FAIL    {name:<12} 模拟失败")
                else:
                    node.state = "SUCCESS"
                    log.append(f"  RUN     {name:<12} 耗时 {node.duration}s")
        return log


dag = DAG()
dag.add("extract_orders", duration=2)
dag.add("extract_users", duration=1)
dag.add("clean_orders", ["extract_orders"], duration=3)
dag.add("join", ["clean_orders", "extract_users"], duration=2)
dag.add("aggregate", ["join"], duration=1)
dag.add("report", ["aggregate"], duration=1)
dag.add("notify", ["report"], duration=0.5)

print("== DAG 校验 ==")
print("  错误:", dag.validate() or "无")

print("\n== 拓扑分层（同层可并行）==")
for i, layer in enumerate(dag.layers(), 1):
    print(f"  第 {i} 层: {layer}")

print("\n== 正常执行 ==")
for line in dag.run():
    print(line)
print("  最终状态:", {n: v.state for n, v in dag.nodes.items()})

print("\n== 上游失败 -> 下游跳过 ==")
dag2 = DAG()
dag2.add("a"); dag2.add("b", ["a"]); dag2.add("c", ["b"]); dag2.add("d", ["a"])
for line in dag2.run(fail={"b"}):
    print(line)
print("  最终状态:", {n: v.state for n, v in dag2.nodes.items()})
print("  注意 d 只依赖 a，a 成功所以 d 照常执行，不受 b 失败影响")

print("\n== 环检测 ==")
cyc = DAG()
cyc.add("x", ["z"]); cyc.add("y", ["x"]); cyc.add("z", ["y"])
print("  validate:", cyc.validate())
try:
    cyc.layers()
except RuntimeError as e:
    print("  layers 抛出:", e)

print("\n== 缺失依赖 ==")
miss = DAG()
miss.add("only", ["ghost"])
print("  validate:", miss.validate())

print("\n== 关键路径（串行总耗时下界）==")
# 每个节点的最早完成时间 = max(上游完成时间) + 自身耗时
finish = {}
for layer in dag.layers():
    for name in layer:
        deps = dag.nodes[name].deps
        finish[name] = max((finish[d] for d in deps), default=0) + dag.nodes[name].duration
print("  各节点最早完成时间:", {k: round(v, 1) for k, v in finish.items()})
print("  关键路径长度:", max(finish.values()), "秒（并行也无法短于它）")

print("\n== 工程要点 ==")
for line in [
    "注册期做 validate，运行期只按 layers 调度，职责分离",
    "同层任务用线程池/协程并行；跨层用屏障同步",
    "失败传播要区分「硬依赖」与「软依赖」（允许降级）",
    "生产 DAG 还要支持重跑单节点、回填、并发上限与优先级",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 critical_path() 返回具体的关键节点序列，而不只是长度。
# 2. 增加「软依赖」类型：上游失败时下游仍可 RUN（走降级数据）。
# 3. 给 run 增加并发上限，模拟同层任务排队执行的调度日志。
# 4. 思考：为什么要在注册期检测环，而不是运行时靠超时发现？
