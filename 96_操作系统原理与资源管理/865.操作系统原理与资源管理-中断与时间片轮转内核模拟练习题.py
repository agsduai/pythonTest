# ===== 第865课：操作系统原理与资源管理-中断与时间片轮转内核模拟 =====
# 知识点：
#   - 现代内核 = 一个「事件驱动的循环」：时钟中断、系统调用陷入、I/O 中断
#   - 时钟中断：固定间隔打断 CPU，内核收回控制权 -> 时间片轮转成为可能
#   - 系统调用（trap）：进程主动让出/请求 I/O；I/O 完成中断唤醒阻塞进程
#   - 进程状态机：new -> ready -> running -> (blocked <-> ready) -> exit
#   - 本课用 tick 驱动模拟，把 859 课的调度放进中断框架
# 依赖：无（标准库）
from collections import deque


class Proc:
    def __init__(self, pid, arrive, burst, io_at=None, io_len=0):
        self.pid = pid
        self.arrive = arrive
        self.burst = burst          # 总 CPU 需求
        self.io_at = io_at          # 累计运行 io_at 个 tick 后发起 IO
        self.io_len = io_len
        self.remain = burst
        self.cpu_used = 0
        self.state = "new"

    def __repr__(self):
        return f"P{self.pid}"


def simulate(procs, quantum=3, max_ticks=80):
    ready = deque()
    io_wakeup = {}                     # tick -> [pid]
    finish = {}
    trace = []                         # (tick, pid 或 None)
    log = []
    running = None
    t = 0
    pending = sorted(procs, key=lambda p: (p.arrive, p.pid))
    arrived_i = 0
    total = len(procs)

    while t < max_ticks and len(finish) < total:
        # 1) 进程到达（由 fork 系统调用创建）
        while arrived_i < len(pending) and pending[arrived_i].arrive == t:
            p = pending[arrived_i]
            p.state = "ready"
            ready.append(p)
            log.append(f"tick{t:>3}: P{p.pid} fork -> 就绪队列")
            arrived_i += 1
        # 2) I/O 完成中断
        for pid in io_wakeup.pop(t, []):
            p = next(x for x in procs if x.pid == pid)
            p.state = "ready"
            ready.append(p)
            log.append(f"tick{t:>3}: [IO中断] P{p.pid} I/O 完成 -> 就绪")
        # 3) 时钟中断：上一片用尽或运行者为空 -> 调度
        if running is None and ready:
            running = ready.popleft()
            running.state = "running"
            log.append(f"tick{t:>3}: [时钟] 调度 P{running.pid} 上 CPU")
        # 4) 执行一个 tick
        if running is not None:
            p = running
            trace.append((t, p.pid))
            p.remain -= 1
            p.cpu_used += 1
            if p.remain == 0:
                log.append(f"tick{t:>3}: P{p.pid} exit 系统调用 -> 终止")
                finish[p.pid] = t + 1
                p.state = "exit"
                running = None
            elif p.io_at is not None and p.cpu_used == p.io_at:
                p.state = "blocked"
                io_wakeup.setdefault(t + p.io_len, []).append(p.pid)
                log.append(f"tick{t:>3}: P{p.pid} read 系统调用 -> 阻塞等 I/O ({p.io_len} tick)")
                running = None
            elif p.cpu_used % quantum == 0:
                log.append(f"tick{t:>3}: [时钟中断] P{p.pid} 时间片用尽 -> 回就绪队列")
                p.state = "ready"
                ready.append(p)
                running = None
        else:
            trace.append((t, None))
        t += 1

    return trace, log, finish


print("== 进程集 ==")
procs = [
    Proc(1, 0, 8, io_at=4, io_len=3),      # 跑 4 tick 后要读盘
    Proc(2, 1, 6, io_at=5, io_len=2),
    Proc(3, 2, 7),
]
for p in procs:
    print(f"  P{p.pid}: arrive={p.arrive} burst={p.burst} "
          f"io_at={p.io_at} io_len={p.io_len}")
print("  时间片量子 = 3")

print("\n== 运行时间线（每字符 1 tick，'.'=空闲）==")
trace, log, finish = simulate(procs)
line = "".join(str(pid) if pid else "." for _, pid in trace)
print(f"  {line}")
print(f"  总 tick = {len(trace)}，完成 {len(finish)}/3")

print("\n== 事件日志（中断与系统调用）==")
for entry in log:
    print("  ", entry)

print("\n== 进程统计 ==")
print(f"  {'进程':<6}{'到达':>5}{'完成':>5}{'周转':>5}{'等待':>5}")
for p in procs:
    turn = finish[p.pid] - p.arrive
    print(f"  P{p.pid:<5}{p.arrive:>5}{finish[p.pid]:>5}{turn:>5}{turn - p.burst:>5}")

print("\n== 状态迁移要点 ==")
for line in (
    "  时钟中断是抢占的物理基础：没有它，内核无法收回 CPU",
    "  read 系统调用让进程从 running 转 blocked，CPU 立即调度他人",
    "  I/O 完成由设备中断通知内核，进程被重新放回就绪队列",
    "  阻塞期不占 CPU：P1 阻塞的 3 个 tick 里 P2/P3 前进 —— I/O 重叠",
):
    print("  -", line)

print("\n== 与无 IO 的对比 ==")
procs2 = [Proc(1, 0, 8), Proc(2, 1, 6), Proc(3, 2, 7)]
trace2, log2, finish2 = simulate(procs2)
print(f"  无 I/O 时间线: {''.join(str(pid) if pid else '.' for _, pid in trace2)}")
print(f"  总 tick = {len(trace2)} vs 有 I/O = {len(trace)}")
print("  I/O 让总时长变短是错觉？不 —— 是重叠让 CPU 在等待期去跑别的进程")

print("\n== 小结 ==")
for line in (
    "  内核主循环 = 处理到达 -> 处理 I/O 中断 -> 时钟调度 -> 执行 1 tick",
    "  状态机的每次迁移都由一个明确事件（中断/trap）触发",
    "  中断处理要快、上下文要小 —— 这是内核代码的铁律",
    "  下一课综合：把调度、内存、I/O 组装成迷你 OS",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现中断嵌套：I/O 完成中断到达时若恰逢时钟中断，先处理高优先级中断并记录。
# 2. 加入优先级抢占：高优先级进程就绪时立即打断低优先级运行者（preempt）。
# 3. 统计每种事件类型（时钟/IO/系统调用）的触发次数，画成文本直方图。
# 4. 思考：如果时钟中断频率翻倍，系统吞吐和交互延迟各如何变化？开销来自哪里？
