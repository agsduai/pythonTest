# ===== 第642课：定时任务与调度系统-综合案例-轻量作业调度器 =====
# 知识点：
#   - 综合串起本章：cron/间隔触发、优先堆、虚拟时钟、幂等键、重试退避、DAG 依赖、抖动
#   - 调度器分层：Job 定义 -> Trigger 计算下次时间 -> Queue 排序 -> Executor 执行 -> Store 记录
#   - 全部组件可注入：clock（虚拟时钟）、rng（可复现抖动）、store（JSON 持久化）
#   - 执行链：幂等检查 -> 依赖检查 -> 带退避执行 -> 记状态 -> 重新入堆
#   - 无真实 sleep / 无常驻循环，run_until(end) 一次跑完，离线可验证
#   - 与生产调度器（APScheduler/Airflow）的差距只在持久化、并发与分布式锁
# 依赖：无（标准库）
import heapq
import itertools
import json
import random
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Job:
    name: str
    interval: float
    deps: list = field(default_factory=list)
    jitter: float = 0.0
    max_attempts: int = 1
    fail_until: int = 0          # 前 N 次执行抛错，用于演示重试
    next_run: float = 0.0
    runs: int = 0


class VirtualClock:
    def __init__(self, now=0.0):
        self.now = now

    def advance(self, dt):
        self.now += dt


class Store:
    """幂等状态存储：记录已成功完成的 (job, 窗口)。"""

    def __init__(self, path=None):
        self.path = path
        self.done = {}
        if path and path.exists():
            self.done = json.loads(path.read_text("utf-8"))

    def is_done(self, key):
        return key in self.done

    def mark(self, key, value):
        self.done[key] = value
        if self.path:
            self.path.write_text(json.dumps(self.done, ensure_ascii=False), "utf-8")


class Scheduler:
    def __init__(self, clock=None, rng=None, store=None):
        self.clock = clock or VirtualClock()
        self.rng = rng or random.Random(7)
        self.store = store or Store()
        self.jobs = {}
        self.heap = []
        self.seq = itertools.count()
        self.log = []
        self.results = {}

    def add(self, job: Job):
        self.jobs[job.name] = job
        heapq.heappush(self.heap, (job.next_run, next(self.seq), job.name))

    def _reschedule(self, job, run_at):
        job.next_run = run_at + job.interval
        if job.jitter:
            job.next_run += self.rng.uniform(-job.jitter, job.jitter)
            job.next_run = max(self.clock.now + 0.001, job.next_run)
        heapq.heappush(self.heap, (job.next_run, next(self.seq), job.name))

    def _deps_ok(self, job, window):
        return all(self.store.is_done(f"{d}#{window}") for d in job.deps)

    def _execute(self, job, window, run_at):
        """带指数退避的执行（虚拟等待，只累加到 clock）。"""
        key = f"{job.name}#{window}"
        if self.store.is_done(key):
            self.log.append(f"  SKIP  {key:<24} 幂等命中")
            return
        if not self._deps_ok(job, window):
            self.log.append(f"  BLOCK {key:<24} 上游未完成")
            return
        for attempt in range(1, job.max_attempts + 1):
            if attempt > 1:
                delay = min(8, 2 ** (attempt - 2))
                self.clock.advance(delay)
                self.log.append(f"  WAIT  {key:<24} 退避 {delay}s 后重试")
            job.runs += 1
            if job.runs <= job.fail_until:
                if attempt == job.max_attempts:
                    self.log.append(f"  FAIL  {key:<24} 重试耗尽，进死信")
                continue
            result = f"{job.name}@t={run_at:g}"
            self.store.mark(key, result)
            self.results[job.name] = result
            suffix = f"（第 {attempt} 次成功）" if attempt > 1 else ""
            self.log.append(f"  OK    {key:<24} -> {result}{suffix}")
            return

    def run_until(self, end, step=1.0):
        """虚拟时钟推进到 end，触发所有到期任务。"""
        while self.clock.now <= end:
            now = self.clock.now
            due = []
            while self.heap and self.heap[0][0] <= now:
                run_at, _, name = heapq.heappop(self.heap)
                due.append((run_at, name))
            for run_at, name in sorted(due):
                job = self.jobs[name]
                window = int(run_at // job.interval) if job.interval else 0
                self._execute(job, window, run_at)
                self._reschedule(job, run_at)
            self.clock.advance(step)
        return self.log


print("== 构建作业 DAG：extract -> transform -> report ==")
with tempfile.TemporaryDirectory() as tmp:
    store = Store(Path(tmp) / "state.json")
    sch = Scheduler(clock=VirtualClock(), rng=random.Random(7), store=store)
    sch.add(Job("extract", interval=10, jitter=0.5))
    sch.add(Job("transform", interval=10, deps=["extract"], fail_until=2, max_attempts=3))
    sch.add(Job("report", interval=10, deps=["transform"]))
    # 手动固定到 t=0 首次触发，避免 jitter 影响首轮
    for j in sch.jobs.values():
        j.next_run = 0.0
    sch.heap = []
    for j in sch.jobs.values():
        heapq.heappush(sch.heap, (0.0, next(sch.seq), j.name))

    lines = sch.run_until(30, step=1.0)
    print("\n".join(lines[:26]))
    print(f"  ... 共 {len(lines)} 条事件")

    print("\n== 最终状态 ==")
    print("  各作业执行次数:", {n: j.runs for n, j in sch.jobs.items()})
    print("  已成功窗口数:", len(store.done))
    print("  最后结果:", sch.results)

    print("\n== 持久化后重启：幂等不重复 ==")
    store2 = Store(Path(tmp) / "state.json")
    print("  重载已完成键数:", len(store2.done))
    sch2 = Scheduler(store=store2)
    sch2.add(Job("extract", interval=10))
    for j in sch2.jobs.values():
        j.next_run = 0.0
    sch2.heap = [(0.0, next(sch2.seq), "extract")]
    lines2 = sch2.run_until(0, step=1.0)
    print("  重启后首次触发:", lines2[0].strip() if lines2 else "(无)")
    print("  extract 是否被调用:", sch2.jobs["extract"].runs == 0)

print("\n== 分层回顾 ==")
for line in [
    "Job       : 名称 / 间隔 / 依赖 / 抖动 / 重试策略",
    "Trigger   : next_run = 上次 run_at + interval ± jitter（不漂移）",
    "Queue     : heapq 按 (next_run, seq) 取最近任务",
    "Executor  : 幂等检查 -> 依赖检查 -> 退避重试 -> 记状态",
    "Store     : JSON 持久化，重启后仍识别已完成窗口",
]:
    print("  -", line)

print("\n== 与生产调度器的差距 ==")
for line in [
    "并发：真实用线程池/asyncio，本例串行模拟",
    "锁：多实例需分布式锁，防止同一作业被跑两次",
    "时钟：真实用 time.sleep(下次触发 - now)，本例虚拟步进",
    "可观测：还需指标、告警、执行历史与手动补跑入口",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给 Scheduler 增加 cron 触发类型（复用第635课的 parse/matches）。
# 2. 实现 pause(name)/resume(name)，暂停期间不触发也不重排。
# 3. 增加执行超时，超时后按失败处理并触发下一轮重试。
# 4. 思考：为什么 next_run 用「上次 run_at + interval」而不是「now + interval」？
