# ===== 第670课：有限状态机与工作流-工作流引擎与并行分支 =====
# 知识点：
#   - 工作流是「多实例、有向图」的 FSM：节点是任务，边是流转条件
#   - 串行 / 并行分支（fork-join）：AND 汇聚要等所有分支完成
#   - 令牌 token：每个分支持有一个 token，join 处收集齐才继续
#   - 与第641课 DAG 的区别：工作流有「运行时状态」，可长期挂起、可回退
#   - 条件分支（XOR）按 ctx 选择一条边；会签（AND）要求全部通过
#   - 用可注入的 executor 驱动，不真实 sleep，执行日志完整可审计
# 依赖：无（标准库）
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class Node:
    name: str
    kind: str                 # task / fork / join / xor / end
    next: list = field(default_factory=list)
    join_count: int = 0       # join 节点需要收集的分支数


@dataclass
class Instance:
    tokens: dict = field(default_factory=lambda: defaultdict(int))  # node -> 到达次数
    ctx: dict = field(default_factory=dict)
    log: list = field(default_factory=list)
    done: set = field(default_factory=set)


class Workflow:
    def __init__(self, nodes, executor=None):
        self.nodes = {n.name: n for n in nodes}
        self.executor = executor or (lambda name, ctx: "OK")

    def run(self, start, ctx=None, max_steps=100):
        inst = Instance(ctx=ctx or {})
        queue = [start]
        steps = 0
        while queue and steps < max_steps:
            name = queue.pop(0)
            node = self.nodes[name]
            steps += 1
            inst.tokens[name] += 1

            if node.kind == "join":
                need = node.join_count or len(node.next) or 1
                inst.log.append(f"JOIN  {name}: 已到 {inst.tokens[name]}/{need}")
                if inst.tokens[name] < need:
                    continue                          # 等其他分支
                inst.log.append(f"      {name} 汇聚完成")

            elif node.kind == "task":
                result = self.executor(name, inst.ctx)
                inst.log.append(f"TASK  {name} -> {result}")
                inst.done.add(name)

            elif node.kind == "fork":
                inst.log.append(f"FORK  {name} -> {node.next}（并行 {len(node.next)} 路）")

            elif node.kind == "xor":
                branch = self.executor(name, inst.ctx)
                chosen = branch if branch in node.next else node.next[0]
                inst.log.append(f"XOR   {name} -> 选 {chosen}")
                node_next = [chosen]
                queue.extend(node_next)
                continue

            elif node.kind == "end":
                inst.log.append(f"END   {name}")
                continue

            for nxt in node.next:
                queue.append(nxt)
        inst.steps = steps
        return inst


NODES = [
    Node("提交申请", "task", ["并行审批"]),
    Node("并行审批", "fork", ["技术评审", "财务评审", "法务评审"]),
    Node("技术评审", "task", ["汇聚"]),
    Node("财务评审", "task", ["汇聚"]),
    Node("法务评审", "task", ["汇聚"]),
    Node("汇聚", "join", ["条件分流"], join_count=3),
    Node("条件分流", "xor", ["经理签批", "自动通过"]),
    Node("经理签批", "task", ["归档"]),
    Node("自动通过", "task", ["归档"]),
    Node("归档", "task", ["结束"]),
    Node("结束", "end"),
]


def executor(name, ctx):
    if name == "条件分流":
        return "经理签批" if ctx.get("amount", 0) > 10000 else "自动通过"
    if "评审" in name:
        return f"{name}通过"
    return "完成"

print("== 工作流定义 ==")
for n in NODES:
    print(f"  {n.name:<8} {n.kind:<5} -> {n.next}")

print("\n== 大额申请（走经理签批）==")
inst = Workflow(NODES, executor).run("提交申请", {"amount": 50000})
for line in inst.log:
    print("  " + line)
print(f"  步数={inst.steps}  已完成任务={sorted(inst.done)}")

print("\n== 小额申请（自动通过）==")
inst2 = Workflow(NODES, executor).run("提交申请", {"amount": 500})
for line in inst2.log:
    print("  " + line)

print("\n== AND 汇聚：三条分支必须都到齐 ==")
# 手动模拟 join 逐条收集分支 token
demo = Instance()
for branch in ("技术评审", "财务评审", "法务评审"):
    demo.tokens["汇聚"] += 1
    print(f"  收到 {branch} 后，汇聚计数={demo.tokens['汇聚']}/3 "
          f"{'放行' if demo.tokens['汇聚'] >= 3 else '继续等待'}")
print("  结论：少一路就永久挂起 -> 生产需设超时与补偿（第639/44章）")

print("\n== 工作流 vs DAG ==")
for line in (
    "  DAG（第641课）: 一次性批处理，跑完即结束，无中间状态",
    "  工作流        : 可挂起数天等人审批，状态要持久化、可恢复",
    "  工作流支持回退/驳回/会签/委派，DAG 通常不支持",
    "  共同点: 都要环检测、都要失败传播、都要可观测日志",
):
    print(" ", line)

print("\n== 令牌与持久化 ==")
for line in [
    "  每个活跃分支一个 token，join 消费 N 个再产生 1 个",
    "  实例状态 = 当前 token 位置 + ctx + 历史日志，存 DB 即可恢复",
    "  幂等：同一 task 重复投递靠 token 去重，避免重复审批",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 增加「驳回」边：任意评审可回到「提交申请」，并限制最多驳回 3 次。
# 2. 实现 OR 汇聚（任一支到齐即继续），对比 AND 汇聚的日志差异。
# 3. 给 join 增加超时：等待超过 N 步自动走「人工介入」分支。
# 4. 思考：为什么工作流实例必须持久化 token，而不能只存在内存里？
