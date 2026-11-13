# ===== 第337课：算法进阶-综合案例-任务调度器 =====
# 知识点：
#   - 综合运用：拓扑排序（333）+ 堆优先级（331）+ 依赖校验
#   - 场景：任务有依赖关系，依赖满足后按优先级依次执行
#   - 架构思想：入度为 0 的任务进堆，执行后“解锁”后继任务
# 依赖：无

import heapq

# (任务名, 优先级(小=先执行), 依赖列表)
tasks = {
    "拉取代码":   (1, []),
    "安装依赖":   (2, ["拉取代码"]),
    "跑单元测试": (1, ["安装依赖"]),
    "构建镜像":   (2, ["安装依赖"]),
    "部署上线":   (1, ["跑单元测试", "构建镜像"]),
    "发通知":     (5, ["部署上线"]),
}


def schedule(tasks):
    indegree = {name: len(deps) for name, (_, deps) in tasks.items()}
    dependents = {name: [] for name in tasks}
    for name, (_, deps) in tasks.items():
        for d in deps:
            dependents[d].append(name)

    ready = [(prio, name) for name, (prio, deps) in tasks.items() if not deps]
    heapq.heapify(ready)                     # 优先级堆

    order, step = [], 1
    while ready:
        prio, name = heapq.heappop(ready)
        order.append(name)
        print(f"  第{step}步 [P{prio}] 执行：{name}")
        for nxt in dependents[name]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                heapq.heappush(ready, (tasks[nxt][0], nxt))
        step += 1

    if len(order) != len(tasks):
        missing = set(tasks) - set(order)
        raise ValueError(f"存在循环依赖，无法调度的任务：{missing}")
    return order


print("== 调度结果 ==")
order = schedule(tasks)
print("执行顺序：", " → ".join(order))

# 循环依赖演示
bad = dict(tasks, 部署上线=(1, ["发通知"]))     # 让“部署上线”反过来依赖“发通知”
try:
    schedule(bad)
except ValueError as exc:
    print("捕获：", exc)

# ===== 练习题 =====
# 1. 给任务加“耗时”，输出每个任务的实际开始时间（关键路径思想）。
# 2. 同优先级时按“依赖数最少的先执行”改进比较键。
# 3. 思考：这个调度器和第299课的 git 自动存档、第280课定时执行，各解决什么维度的问题？
