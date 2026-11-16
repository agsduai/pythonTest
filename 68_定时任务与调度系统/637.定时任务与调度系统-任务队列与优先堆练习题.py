# ===== 第637课：定时任务与调度系统-任务队列与优先堆 =====
# 知识点：
#   - heapq 实现最小堆：heappush / heappop 都是 O(log n)
#   - 调度器按「下次触发时间」建堆，每次取堆顶即最近要跑的任务
#   - 堆元素用 (run_at, seq, task)：seq 打破时间相同导致的可比较对象报错
#   - 周期任务跑完后重新计算下一次 run_at 再 push 回去，形成循环
#   - 取消用「墓碑标记」（惰性删除）：不真的从堆里移除，弹出时跳过
#   - 虚拟时钟驱动，不真实 sleep；同一时刻多个任务按 seq 稳定排序
# 依赖：无（标准库）
import heapq
import itertools
from dataclasses import dataclass, field


@dataclass
class Task:
    name: str
    interval: float
    run_at: float = 0.0
    cancelled: bool = False
    runs: int = 0


class Scheduler:
    def __init__(self):
        self.heap = []
        self.seq = itertools.count()
        self.tasks = {}
        self.log = []

    def add(self, task: Task):
        self.tasks[task.name] = task
        heapq.heappush(self.heap, (task.run_at, next(self.seq), task.name))

    def cancel(self, name):
        if name in self.tasks:
            self.tasks[name].cancelled = True     # 墓碑标记

    def pop_due(self, now):
        """弹出所有 run_at <= now 的任务名（含惰性删除过滤）。"""
        due = []
        while self.heap and self.heap[0][0] <= now:
            run_at, _, name = heapq.heappop(self.heap)
            t = self.tasks.get(name)
            if t is None or t.cancelled:
                continue                          # 跳过已取消
            due.append((run_at, name))
        return due

    def fire(self, run_at, name, now):
        """执行并把周期任务重新入堆。"""
        t = self.tasks[name]
        t.runs += 1
        self.log.append((now, name, run_at))
        if t.interval > 0:
            t.run_at = run_at + t.interval         # 按原排期推进，不漂移
            heapq.heappush(self.heap, (t.run_at, next(self.seq), name))

    def run_until(self, end, step=1.0):
        """虚拟时钟从 0 推进到 end，逐步触发到期任务。"""
        now = 0.0
        while now <= end:
            for run_at, name in self.pop_due(now):
                self.fire(run_at, name, now)
            now += step


print("== 建堆与取出顺序 ==")
s = Scheduler()
for t in (Task("report", 10, run_at=5), Task("heartbeat", 3, run_at=0),
          Task("cleanup", 30, run_at=2), Task("sync", 5, run_at=5)):
    s.add(t)
print("  初始堆（按 run_at, seq）:", [(round(a, 1), n) for a, _, n in sorted(s.heap)])
print("  同一时刻的 report/sync 靠 seq 稳定排序，不会比较 Task 对象")

print("\n== 虚拟时钟跑到 t=16 ==")
s.log.clear()
# 手动逐步驱动，便于观察
now = 0.0
while now <= 16:
    for run_at, name in s.pop_due(now):
        s.fire(run_at, name, now)
    now += 1
for now, name, run_at in s.log:
    print(f"  t={now:>4.0f}  触发 {name:<10} (计划 run_at={run_at:>4.0f})")
print("  各任务执行次数:", {k: v.runs for k, v in s.tasks.items()})

print("\n== 取消（墓碑标记）==")
s2 = Scheduler()
s2.add(Task("a", 2, run_at=0))
s2.add(Task("b", 2, run_at=0))
s2.cancel("b")
now = 0.0
while now <= 6:
    for run_at, name in s2.pop_due(now):
        s2.fire(run_at, name, now)
    now += 1
print("  a 执行次数:", s2.tasks["a"].runs, " b 执行次数:", s2.tasks["b"].runs)
print("  堆里残留的 b 条目数:", sum(1 for _, _, n in s2.heap if n == "b"),
      "（惰性删除：下次弹出时跳过）")

print("\n== 一次性任务（interval=0）==")
s3 = Scheduler()
s3.add(Task("once", 0, run_at=3))
s3.run_until(10)
print("  执行次数:", s3.tasks["once"].runs, "（只跑一次，不再入堆）")

print("\n== 复杂度 ==")
for line in (
    "  heappush / heappop : O(log n)",
    "  查看最近任务       : O(1)（heap[0]）",
    "  遍历全部任务       : O(n)，不适合放进热路径",
    "  n=10 万任务时 log n≈17，仍远优于每分钟全表扫描",
):
    print(line)

print("\n== 与真实调度器的差距 ==")
for line in [
    "这里用虚拟时钟步进；真实调度器用 time.sleep(下一次 - now) 精确等待",
    "需处理并发执行、超时、失败重试、持久化（重启后不丢任务）",
    "多实例部署要加分布式锁，避免同一任务被跑多次",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 cancel 的「立即物理删除」版本，对比与惰性删除的复杂度。
# 2. 增加任务优先级字段，让堆按 (run_at, priority, seq) 排序。
# 3. 给 fire 增加最大执行时长，超时后记录告警并跳过下一轮。
# 4. 思考：为什么重新入堆用 run_at + interval，而不是 now + interval？
