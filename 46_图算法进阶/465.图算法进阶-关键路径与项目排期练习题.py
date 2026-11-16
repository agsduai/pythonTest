# ===== 第465课：图算法进阶-关键路径与项目排期 =====
# 知识点：
#   - AOE 网：节点是事件、边是任务（带工期），用于项目排期
#   - 最早开始 ES / 最早完成 EF：正向拓扑推进，EF = ES + 工期
#   - 最晚开始 LS / 最晚完成 LF：反向拓扑推进，LS = LF - 工期
#   - 总浮动时间（slack）= LS - ES；slack=0 的任务在关键路径上
#   - 关键路径 = 项目最短总工期；任一关键任务延期，项目就延期
#   - 与第333课拓扑排序、第460课最长路思想的关系
from collections import defaultdict, deque


def critical_path(tasks: dict):
    """tasks: {任务名: (工期, [前置任务])}
    返回 (project_duration, es, ef, ls, lf, slack, critical_tasks)。
    """
    # 1) 建前驱/后继与入度
    indegree = {name: len(preds) for name, (_, preds) in tasks.items()}
    successors = defaultdict(list)
    for name, (_, preds) in tasks.items():
        for p in preds:
            successors[p].append(name)

    # 2) 拓扑序（Kahn）
    queue = deque([n for n, d in indegree.items() if d == 0])
    topo = []
    while queue:
        node = queue.popleft()
        topo.append(node)
        for nxt in successors[node]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    if len(topo) != len(tasks):
        raise ValueError("任务依赖中存在环，无法排期")

    # 3) 正向：最早开始/完成
    es, ef = {}, {}
    for node in topo:
        duration, preds = tasks[node]
        es[node] = max((ef[p] for p in preds), default=0)
        ef[node] = es[node] + duration

    project_duration = max(ef.values())

    # 4) 反向：最晚完成/开始
    ls, lf = {}, {}
    for node in reversed(topo):
        duration, _ = tasks[node]
        succ = successors[node]
        lf[node] = min((ls[s] for s in succ), default=project_duration)
        ls[node] = lf[node] - duration

    # 5) 浮动时间与关键任务
    slack = {n: ls[n] - es[n] for n in tasks}
    critical = [n for n in topo if slack[n] == 0]

    return project_duration, es, ef, ls, lf, slack, critical


# ---- 项目：开发一个功能上线的任务图 ----
# 任务名: (工期天数, [前置任务])
TASKS = {
    "需求分析": (3, []),
    "原型设计": (2, ["需求分析"]),
    "数据库设计": (2, ["需求分析"]),
    "后端开发": (5, ["数据库设计", "原型设计"]),
    "前端开发": (4, ["原型设计"]),
    "联调": (2, ["后端开发", "前端开发"]),
    "测试": (3, ["联调"]),
    "上线": (1, ["测试"]),
}

duration, es, ef, ls, lf, slack, critical = critical_path(TASKS)
print("== 项目排期表（单位：天）==")
print(f"  {'任务':<10}{'工期':>4}{'ES':>5}{'EF':>5}{'LS':>5}{'LF':>5}{'浮动':>5}  关键?")
for name in TASKS:
    print(f"  {name:<10}{TASKS[name][0]:>4}{es[name]:>5}{ef[name]:>5}"
          f"{ls[name]:>5}{lf[name]:>5}{slack[name]:>5}  {'★' if slack[name] == 0 else ''}")

print(f"\n项目最短工期：{duration} 天")
print("关键路径：", " → ".join(critical))
print("（关键任务浮动为 0，任何延期都会直接推迟上线）")

# ---- 非关键任务可以拖几天 ----
print("\n== 非关键任务的缓冲 ==")
for name in TASKS:
    if slack[name] > 0:
        print(f"  {name}: 可延迟 {slack[name]} 天不影响上线")

# ---- 如果关键任务延期 2 天 ----
print("\n== 模拟：后端开发延期 2 天 ==")
TASKS_DELAYED = dict(TASKS)
TASKS_DELAYED["后端开发"] = (7, TASKS["后端开发"][1])
d2, es2, _, _, _, slack2, critical2 = critical_path(TASKS_DELAYED)
print("  新工期：", d2, "天（原", duration, "天）")
print("  新关键路径：", " → ".join(critical2))

# ---- 如果非关键任务延期（不影响总工期）----
print("\n== 模拟：前端开发延期 1 天（原浮动 1 天）==")
TASKS_DELAYED2 = dict(TASKS)
TASKS_DELAYED2["前端开发"] = (5, TASKS["前端开发"][1])
d3, _, _, _, _, slack3, critical3 = critical_path(TASKS_DELAYED2)
print("  新工期：", d3, "天 | 前端开发浮动：", slack3["前端开发"])
print("  说明：浮动刚好用完，前端开发也变成了关键任务")

# ---- 应用扩展 ----
print("\n== 应用 ==")
for item in [
    "项目排期：识别关键任务，优先保障资源",
    "资源优化：非关键任务错峰，避免人力冲突",
    "风险预警：关键任务进度落后立即告警",
    "与第333课拓扑排序：关键路径是在拓扑序上做两遍 DP",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 增加“人力”字段，计算每天需要多少人（资源直方图）。
# 2. 输出所有关键路径（可能不止一条）。
# 3. 加入“赶工成本”，求在预算内压缩工期的最优方案。
# 4. 思考：为什么关键路径上的任务不能简单“并行化”来缩短工期？
