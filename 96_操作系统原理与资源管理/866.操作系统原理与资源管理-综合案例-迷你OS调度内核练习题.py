# ===== 第866课：操作系统原理与资源管理-综合案例-迷你OS调度内核 =====
# 知识点：
#   - 综合：进程表(859) + 伙伴内存(863) + 中断框架(865) + 时间片轮转
#   - 一个进程的完整生命周期：spawn 分配内存 -> ready -> running
#     -> (IO 阻塞 -> ready)* -> exit 释放内存
#   - 系统视图：任意时刻「谁在 CPU 上、谁在就绪、谁阻塞、内存占多少」
#   - 本课把前面的组件拼成一个可观察的内核，并输出运行报告
# 依赖：无（标准库）
from collections import deque


class Buddy:
    def __init__(self, order=6):
        self.order = order
        self.free = {order: [0]}

    def alloc(self, order):
        for o in range(order, self.order + 1):
            if self.free.get(o):
                addr = self.free[o].pop(0)
                while o > order:
                    o -= 1
                    self.free.setdefault(o, []).append(addr + (1 << o))
                return addr, order
        return None

    def release(self, addr, order):
        while order < self.order:
            buddy = addr ^ (1 << order)
            if buddy in self.free.get(order, []):
                self.free[order].remove(buddy)
                addr = min(addr, buddy)
                order += 1
            else:
                break
        self.free.setdefault(order, []).append(addr)

    def used_units(self):
        total_units = 1 << self.order
        free = sum((1 << o) * len(v) for o, v in self.free.items())
        return total_units - free


class Proc:
    def __init__(self, pid, arrive, burst, mem_order, io_at=None, io_len=0):
        self.pid = pid
        self.arrive = arrive
        self.burst = burst
        self.mem_order = mem_order
        self.io_at = io_at
        self.io_len = io_len
        self.remain = burst
        self.cpu_used = 0
        self.state = "new"
        self.mem_addr = None


class MiniOS:
    def __init__(self, quantum=3):
        self.mem = Buddy(order=6)          # 64 单位物理内存
        self.quantum = quantum
        self.procs = []
        self.next_pid = 1

    def spawn(self, arrive, burst, mem_order=2, io_at=None, io_len=0):
        got = self.mem.alloc(mem_order)
        if got is None:
            raise OSError("内存不足，spawn 失败")
        addr, order = got
        p = Proc(self.next_pid, arrive, burst, mem_order, io_at, io_len)
        p.mem_addr = addr
        self.procs.append(p)
        self.next_pid += 1
        return p

    def run(self, max_ticks=100):
        ready = deque()
        io_wake = {}
        finish = {}
        trace = []
        log = []
        mem_hist = []                      # (tick, used)
        pending = sorted(self.procs, key=lambda p: p.arrive)
        i = 0
        running = None
        t = 0
        while t < max_ticks and len(finish) < len(self.procs):
            while i < len(pending) and pending[i].arrive == t:
                p = pending[i]
                p.state = "ready"
                ready.append(p)
                log.append(f"t{t:>3} spawn  P{p.pid} 分配内存@{p.mem_addr}"
                           f"(2^{p.mem_order}) -> 就绪")
                i += 1
            for pid in io_wake.pop(t, []):
                p = next(x for x in self.procs if x.pid == pid)
                p.state = "ready"
                ready.append(p)
                log.append(f"t{t:>3} [IO]   P{p.pid} I/O 完成 -> 就绪")
            if running is None and ready:
                running = ready.popleft()
                running.state = "running"
                log.append(f"t{t:>3} [时钟] 调度 P{running.pid}")
            if running is not None:
                p = running
                trace.append((t, p.pid))
                p.remain -= 1
                p.cpu_used += 1
                if p.remain == 0:
                    self.mem.release(p.mem_addr, p.mem_order)
                    log.append(f"t{t:>3} exit   P{p.pid} 释放内存@{p.mem_addr}")
                    finish[p.pid] = t + 1
                    p.state = "exit"
                    running = None
                elif p.io_at is not None and p.cpu_used == p.io_at:
                    p.state = "blocked"
                    io_wake.setdefault(t + p.io_len, []).append(p.pid)
                    log.append(f"t{t:>3} [trap] P{p.pid} read -> 阻塞 {p.io_len} tick")
                    running = None
                elif p.cpu_used % self.quantum == 0:
                    p.state = "ready"
                    ready.append(p)
                    log.append(f"t{t:>3} [时钟] P{p.pid} 时间片用尽 -> 就绪尾")
                    running = None
            else:
                trace.append((t, None))
            mem_hist.append((t, self.mem.used_units()))
            t += 1
        return trace, log, finish, mem_hist


print("== 启动迷你 OS（内存 64 单位，量子 3）==")
osk = MiniOS(quantum=3)
jobs = [
    (0, 8, 3, 4, 3),      # arrive, burst, mem_order, io_at, io_len
    (1, 6, 2, 5, 2),
    (2, 7, 2, None, 0),
    (4, 5, 4, 2, 4),
]
for arrive, burst, mo, io_at, io_len in jobs:
    p = osk.spawn(arrive, burst, mo, io_at, io_len)
    print(f"  spawn P{p.pid}: burst={burst} mem=2^{mo} ({1 << mo} 单位)@{p.mem_addr}")

print("\n== 运行 ==")
trace, log, finish, mem_hist = osk.run()
print(f"  时间线: {''.join(str(pid) if pid else '.' for _, pid in trace)}")
print(f"  总 tick = {len(trace)}")

print("\n== 内核事件日志 ==")
for entry in log:
    print("  ", entry)

print("\n== 内存占用曲线（每 5 tick 采样）==")
for tick, used in mem_hist[::5]:
    bar = "#" * used
    print(f"  t{tick:>3} {used:>2} {bar}")

print("\n== 进程报告 ==")
print(f"  {'进程':<6}{'到达':>5}{'完成':>5}{'周转':>5}{'等待':>5}{'内存块':>8}")
for p in osk.procs:
    turn = finish[p.pid] - p.arrive
    print(f"  P{p.pid:<5}{p.arrive:>5}{finish[p.pid]:>5}{turn:>5}{turn - p.burst:>5}"
          f"{'2^' + str(p.mem_order):>8}")
print(f"  全部退出后内存空闲链恢复: used = {osk.mem.used_units()} 单位")

print("\n== 内存不足的场景 ==")
tight = MiniOS(quantum=3)              # 64 单位
tight.spawn(0, 5, 4)                   # 16
tight.spawn(0, 5, 4)                   # 16
tight.spawn(0, 5, 4)                   # 16
try:
    tight.spawn(0, 5, 5)               # 需要 32 > 剩余 16
except OSError as exc:
    print(f"  三个 2^4 进程后申请 2^5: {type(exc).__name__}: {exc}")
print("  真实内核会拒绝 fork/返回 ENOMEM —— 内存也是调度的资源约束")

print("\n== 小结 ==")
for line in (
    "  OS = 资源分配器 + 事件循环：spawn 分内存、run 分 CPU、exit 收回一切",
    "  进程状态与内存状态要在同一个循环里联动更新",
    "  资源约束（内存不足）必须显式失败，不能默默超卖",
    "  真实内核还有虚拟内存、页表、权限环 —— 机制分层后各司其职",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 给 MiniOS 加优先级：高优先级进程就绪时抢占当前运行者（记录被抢占时刻）。
# 2. 实现「内存等待队列」：spawn 失败的进程排队，等内存释放后自动启动。
# 3. 输出甘特图 + 状态叠加图：每 tick 显示 CPU 与内存占用的双行视图。
# 4. 思考：如果进程退出时忘记释放内存，迷你 OS 会先出现什么症状？对应真实
#    系统中的什么现象？
