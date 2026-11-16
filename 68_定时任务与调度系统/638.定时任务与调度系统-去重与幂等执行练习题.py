# ===== 第638课：定时任务与调度系统-去重与幂等执行 =====
# 知识点：
#   - 调度器至少一次投递（at-least-once），同一任务可能重复触发，执行体必须幂等
#   - 幂等键 = 任务名 + 逻辑时间窗（如 2026-11-14T09:00），而非随机 UUID
#   - 用 set / 字典记录「已处理的幂等键」，重复到达直接跳过
#   - 状态机：PENDING -> RUNNING -> DONE / FAILED，避免重复 RUNNING
#   - 持久化到 JSON 文件可跨进程重启；写入用「临时文件 + os.replace」保证原子
#   - 与第44章幂等、第53章消息投递语义串联
# 依赖：无（标准库）
import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

PENDING, RUNNING, DONE, FAILED = "PENDING", "RUNNING", "DONE", "FAILED"


@dataclass
class Execution:
    key: str
    state: str = PENDING
    attempts: int = 0
    result: str = ""


class IdempotentRunner:
    def __init__(self, store: Path | None = None):
        self.store = store
        self.records: dict[str, Execution] = {}
        self.events = []
        if store and store.exists():
            for k, v in json.loads(store.read_text("utf-8")).items():
                self.records[k] = Execution(**v)

    def _persist(self):
        if not self.store:
            return
        data = {k: vars(v) for k, v in self.records.items()}
        tmp = self.store.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False), "utf-8")
        os.replace(tmp, self.store)          # 原子替换，避免写一半崩溃

    def run(self, key, work, max_attempts=3):
        rec = self.records.get(key)
        if rec is None:
            rec = Execution(key)
            self.records[key] = rec
        if rec.state == DONE:
            self.events.append(f"SKIP   {key} 已成功，直接返回 {rec.result!r}")
            return rec.result
        if rec.state == RUNNING:
            self.events.append(f"SKIP   {key} 正在执行中")
            return None
        rec.state = RUNNING
        rec.attempts += 1
        self._persist()
        try:
            result = work()
            rec.state, rec.result = DONE, result
            self.events.append(f"OK     {key} 第 {rec.attempts} 次尝试成功 -> {result!r}")
        except Exception as e:
            rec.state = FAILED if rec.attempts >= max_attempts else PENDING
            rec.result = ""
            self.events.append(f"FAIL   {key} 第 {rec.attempts} 次: {e}")
        self._persist()
        return rec.result or None


print("== 同一幂等键重复投递 ==")
runner = IdempotentRunner()
counter = {"n": 0}

def charge():
    counter["n"] += 1
    return f"order-{counter['n']}"

for _ in range(4):
    runner.run("charge#2026-11-14T09:00", charge)
print("\n".join("  " + e for e in runner.events))
print(f"  业务函数实际执行次数: {counter['n']}（应为 1）")

print("\n== 不同时间窗是不同任务 ==")
for window in ("09:00", "09:05", "09:10"):
    runner.run(f"charge#2026-11-14T{window}", charge)
print(f"  业务函数累计执行: {counter['n']}（应为 4）")
print("  记录数:", len(runner.records))

print("\n== 失败重试与最终失败 ==")
attempts = {"n": 0}
def flaky():
    attempts["n"] += 1
    if attempts["n"] < 3:
        raise RuntimeError("下游暂时不可用")
    return "success"

r2 = IdempotentRunner()
for _ in range(5):
    r2.run("sync#batch-7", flaky)
print("\n".join("  " + e for e in r2.events))
print("  最终状态:", r2.records["sync#batch-7"].state)

print("\n== 超过最大尝试次数后不再无限重试 ==")
r3 = IdempotentRunner()
def always_fail():
    raise RuntimeError("永久故障")
for i in range(5):
    r3.run("bad#1", always_fail, max_attempts=2)
print("\n".join("  " + e for e in r3.events))
print("  最终状态:", r3.records["bad#1"].state, "| 尝试次数:", r3.records["bad#1"].attempts)

print("\n== 持久化：重启后仍识别已完成的键 ==")
with tempfile.TemporaryDirectory() as tmp:
    store = Path(tmp) / "state.json"
    r4 = IdempotentRunner(store)
    r4.run("daily#2026-11-14", lambda: "done")
    print(f"  状态文件: {store.read_text('utf-8').strip()}")
    r5 = IdempotentRunner(store)          # 模拟进程重启
    calls = {"n": 0}
    def work():
        calls["n"] += 1
        return "again"
    r5.run("daily#2026-11-14", work)
    print("  重启后重复投递事件:", r5.events[-1])
    print(f"  业务函数是否被调用: {calls['n'] == 0}")
    print("  原子写入：先写 .tmp 再 os.replace，不会出现半截 JSON")

print("\n== 幂等键设计 ==")
for line in [
    "好: f'{job}#{bucket}'，bucket 由触发时间按窗口取整得到",
    "坏: uuid4() —— 每次都不同，等于没去重",
    "坏: 只用 job 名 —— 今天的成功会挡住明天的任务",
    "含业务主键时更精确：'refund#order123#v1'",
]:
    print("  -", line)

print("\n== 工程要点 ==")
for line in [
    "去重表需设 TTL，否则无限增长；按窗口过期清理",
    "DONE 状态要连同结果一起存，重复请求才能返回同样的结果",
    "多实例共享同一份 store（DB/Redis）才能实现全局幂等",
    "业务侧也要幂等（数据库唯一键），不能只靠调度层",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给 IdempotentRunner 增加 TTL 过期清理，丢弃 7 天前的 DONE 记录。
# 2. 实现 RUNNING 超时回收：超过 N 秒未完成则重置为 PENDING。
# 3. 把 store 换成 sqlite3，支持多进程并发安全去重。
# 4. 思考：为什么「至少一次投递 + 幂等执行」比「恰好一次投递」更可实现？
