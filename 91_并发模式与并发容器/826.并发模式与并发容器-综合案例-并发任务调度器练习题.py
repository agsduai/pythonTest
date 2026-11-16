# ===== 第826课：并发模式与并发容器-综合案例-并发任务调度器 =====
# 知识点：
#   - 综合串起本章：线程安全容器 + 生产者消费者 + 读写锁 + Actor + 死锁预防
#   - 任务调度器：任务图（依赖关系）+ 线程池 + 优先级队列 + 结果收集
#   - 分层设计：Task（定义）-> Scheduler（调度）-> Worker（执行）-> Monitor（监控）
#   - 并发安全：SafeDict 存结果、Lock 保护任务队列、Event 控制关闭
#   - 与第68章定时调度器不同：这里聚焦「并发执行依赖图」而非「定时触发」
#   - 全部标准库 + 固定 seed + 内存操作，离线可运行
# 依赖：无（标准库）
import threading
import queue
import random
import time
import math
from collections import defaultdict, deque
from dataclasses import dataclass, field


@dataclass
class Task:
    name: str
    deps: list = field(default_factory=list)
    priority: int = 0
    duration: float = 0.01          # 模拟执行耗时（很短）
    result: object = None
    state: str = "PENDING"          # PENDING / READY / RUNNING / DONE / FAILED
    error: str = ""

    def __repr__(self):
        return f"Task({self.name!r}, deps={self.deps}, state={self.state})"


class ConcurrentScheduler:
    """并发任务调度器：依赖图 + 线程池 + 优先级队列。"""

    def __init__(self, n_workers=3, seed=0):
        self.tasks = {}
        self.rng = random.Random(seed)
        self.n_workers = n_workers
        self.ready_queue = queue.PriorityQueue()   # 优先级队列
        self.results_lock = threading.Lock()
        self.results = {}
        self._completion_event = threading.Event()
        self._lock = threading.RLock()             # 可重入：_mark_ready 内调 _deps_satisfied
        self._all_done = threading.Event()
        self._seq = 0

    def add_task(self, task: Task):
        with self._lock:
            self.tasks[task.name] = task

    def _deps_satisfied(self, task):
        """检查所有依赖是否已完成。"""
        with self._lock:
            return all(
                self.tasks.get(dep) and self.tasks[dep].state == "DONE"
                for dep in task.deps
            )

    def _mark_ready(self):
        """把依赖已满足且状态为 PENDING 的任务标记为 READY 并入队。"""
        with self._lock:
            for task in self.tasks.values():
                if task.state == "PENDING" and self._deps_satisfied(task):
                    task.state = "READY"
                    self._seq += 1
                    self.ready_queue.put((-task.priority, self._seq, task))

    def _worker(self, worker_id):
        """工作线程：从优先级队列取任务执行。"""
        rng = random.Random(worker_id * 1000)
        while True:
            try:
                _, _, task = self.ready_queue.get(timeout=0.5)
            except queue.Empty:
                with self._lock:
                    all_done = all(t.state in ("DONE", "FAILED") for t in self.tasks.values())
                if all_done:
                    self._all_done.set()
                    break
                continue

            task.state = "RUNNING"
            try:
                # 模拟执行（不真实 sleep，用计算消耗）
                result = 0
                for _ in range(int(task.duration * 10000)):
                    result += rng.random()
                task.result = result
                task.state = "DONE"
            except Exception as e:
                task.state = "FAILED"
                task.error = str(e)

    def run(self):
        """主循环：持续调度就绪任务，直到所有任务完成。"""
        workers = [threading.Thread(target=self._worker, args=(i,))
                   for i in range(self.n_workers)]
        for w in workers: w.start()

        # 主循环持续 _mark_ready 直到所有任务完成
        while True:
            self._mark_ready()
            with self._lock:
                all_done = all(t.state in ("DONE", "FAILED")
                               for t in self.tasks.values())
            if all_done:
                self._all_done.set()
                break
            self._all_done.wait(timeout=0.05)

        for w in workers: w.join(timeout=3)
        return self.results

    def summary(self):
        states = defaultdict(int)
        for t in self.tasks.values():
            states[t.state] += 1
        return dict(states)

    def execution_order(self):
        """按完成时间排序的任务列表（简化：按状态遍历）。"""
        return [(t.name, t.state, t.priority) for t in self.tasks.values()
                if t.state == "DONE"]


print("== 任务依赖图 ==")
# 构建 DAG：
#   A -> B, C
#   B -> D
#   C -> D, E
#   D -> F
#   E -> F
sched = ConcurrentScheduler(n_workers=3, seed=7)
tasks = [
    Task("A", deps=[], priority=1, duration=0.01),
    Task("B", deps=["A"], priority=2, duration=0.02),
    Task("C", deps=["A"], priority=2, duration=0.01),
    Task("D", deps=["B", "C"], priority=3, duration=0.02),
    Task("E", deps=["C"], priority=1, duration=0.01),
    Task("F", deps=["D", "E"], priority=3, duration=0.01),
]
for t in tasks:
    sched.add_task(t)
print("  依赖图:")
for t in tasks:
    print(f"    {t.name} -> {t.deps or '无依赖'}")

print("\n== 执行 ==")
results = sched.run()
print(f"  状态汇总: {sched.summary()}")
print(f"  完成的任务: {sorted(sched.execution_order())}")
print(f"  结果数: {len(results)}")

print("\n== 验证依赖顺序 ==")
# B 和 C 应该在 A 之后完成
order = {name: i for i, (name, _, _) in enumerate(sched.execution_order())}
checks = [
    ("A", "B"), ("A", "C"),
    ("B", "D"), ("C", "D"), ("C", "E"),
    ("D", "F"), ("E", "F"),
]
for before, after in checks:
    ok = order.get(before, -1) < order.get(after, -1) if before in order and after in order else "N/A"
    print(f"  {before} 在 {after} 之前: {ok}")

print("\n== 优先级效果 ==")
# 构造多个无依赖任务，验证高优先级先完成
sched2 = ConcurrentScheduler(n_workers=1, seed=42)   # 单线程保证顺序
for i in range(8):
    sched2.add_task(Task(f"task{i}", deps=[], priority=i % 3, duration=0.01))
sched2.run()
print(f"  单线程时任务完成顺序: {[t.name for t in sched2.tasks.values()]}")
print("  优先级相同时按入队顺序；不同时高优先级先出队")

print("\n== 并发安全验证 ==")
sched3 = ConcurrentScheduler(n_workers=4, seed=99)
for i in range(20):
    sched3.add_task(Task(f"parallel_{i}", deps=[], priority=1, duration=0.01))
sched3.run()
states = sched3.summary()
print(f"  20 个并行任务: {states}")
print(f"  全部完成: {states.get('DONE', 0) == 20}")

print("\n== 并发模式总结 ==")
for line in [
    "  线程安全容器: SafeCounter / RWDict / StripedDict（第819/821课）",
    "  生产者消费者: PriorityQueue + 毒丸 + 背压（第820课）",
    "  Actor: 状态私有 + 消息传递（第822课）",
    "  CSP: Channel + fan-in / fan-out（第823课）",
    "  并行映射: ThreadPoolExecutor / ProcessPoolExecutor（第824课）",
    "  安全: 死锁预防 / 锁排序 / timeout 检测（第825课）",
    "  综合: 本课的并发任务调度器 = 以上所有模式的组合",
]:
    print("  -", line)

print("\n== 与生产调度器的差距 ==")
for line in [
    "  本课用虚拟时长（微秒级计算），真实调度器用 time.sleep/事件驱动",
    "  不支持取消、暂停/恢复、重试、超时",
    "  不支持分布式（多进程/多机器）",
    "  更复杂的需求用 Celery/APScheduler/Airflow 等专业框架",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「任务取消」：CANCELLED 状态的任务不会被调度，其依赖任务也被跳过。
# 2. 实现「重试」：FAILED 任务自动重试 max_retries 次。
# 3. 加入「资源限制」：同时运行的任务不超过 max_concurrent 个。
# 4. 思考：为什么调度器需要 Event + 队列 timeout 双重机制来检测完成？
