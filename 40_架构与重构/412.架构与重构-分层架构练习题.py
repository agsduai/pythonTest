# ===== 第412课：架构与重构-分层架构 =====
# 知识点：
#   - 三层：表现层（CLI/HTTP）→ 业务层（Service）→ 数据层（Repository）
#   - 依赖方向只能单向：外层依赖内层，内层不认识外层
#   - Repository 用接口（Protocol）隔离数据库细节，业务层不写 SQL
#   - 好处：换存储/换界面只改一层；业务逻辑可脱离框架测试
#   - 与第209课“连接封装”、第394课“依赖注入”是同一条线的延伸
from dataclasses import dataclass, field
from typing import Protocol


# ---------------- 领域对象 ----------------
@dataclass
class Task:
    id: int
    title: str
    done: bool = False


# ---------------- 数据层接口 ----------------
class TaskRepository(Protocol):

    def add(self, title: str) -> Task: ...
    def all(self) -> list[Task]: ...
    def get(self, task_id: int) -> Task | None: ...
    def save(self, task: Task) -> None: ...


# ---------------- 数据层实现（内存版，可替换为 SQLite）----------------
class InMemoryTaskRepository:

    def __init__(self):
        self._items: dict[int, Task] = {}
        self._next_id = 1

    def add(self, title: str) -> Task:
        task = Task(self._next_id, title)
        self._items[task.id] = task
        self._next_id += 1
        return task

    def all(self) -> list[Task]:
        return list(self._items.values())

    def get(self, task_id: int) -> Task | None:
        return self._items.get(task_id)

    def save(self, task: Task) -> None:
        self._items[task.id] = task


# ---------------- 业务层：只做规则，不碰存储细节 ----------------
class TaskService:

    def __init__(self, repo: TaskRepository):
        self.repo = repo

    def create(self, title: str) -> Task:
        title = title.strip()
        if not title:
            raise ValueError("标题不能为空")
        return self.repo.add(title)

    def complete(self, task_id: int) -> Task:
        task = self.repo.get(task_id)
        if task is None:
            raise LookupError(f"任务 {task_id} 不存在")
        if task.done:
            raise ValueError(f"任务 {task_id} 已完成")
        task.done = True
        self.repo.save(task)
        return task

    def pending(self) -> list[Task]:
        return [t for t in self.repo.all() if not t.done]


# ---------------- 表现层：只负责输入输出，不写业务规则 ----------------
def run_cli(service: TaskService, commands: list[tuple]):
    for action, *args in commands:
        try:
            if action == "add":
                task = service.create(args[0])
                print(f"  + 新建 #{task.id} {task.title}")
            elif action == "done":
                task = service.complete(int(args[0]))
                print(f"  ✓ 完成 #{task.id} {task.title}")
            elif action == "list":
                print("  待办：", [(t.id, t.title) for t in service.pending()])
        except (ValueError, LookupError) as exc:
            print(f"  ✗ {exc}")


print("== 内存仓库 ==")
run_cli(TaskService(InMemoryTaskRepository()), [
    ("add", "写周报"),
    ("add", "买咖啡"),
    ("done", "1"),
    ("done", "1"),          # 重复完成 → 业务错误
    ("list",),
])

# ---- 换存储：只需实现同一个 Protocol，业务层与表现层零改动 ----
class FakeRepo(InMemoryTaskRepository):
    """演示：把 id 从 100 开始，模拟另一个数据源。"""

    def __init__(self):
        super().__init__()
        self._next_id = 100


print("\n== 换一个仓库实现 ==")
run_cli(TaskService(FakeRepo()), [("add", "来自新仓库"), ("list",)])

# 分层检查清单：
#   ☑ 业务层有没有 import sqlite3 / requests / argparse？——不应该有
#   ☑ 表现层有没有 if 业务规则？——不应该有
#   ☑ 数据层有没有打印语句？——不应该有

# ===== 练习题 =====
# 1. 实现 SqliteTaskRepository（支持传入连接字符串），替换内存版。
# 2. 给 Service 加 rename(task_id, new_title)，并补错误处理。
# 3. 把 run_cli 换成 HTTP 表现层（复用第410课框架）。
# 4. 思考：为什么“业务层不依赖数据库”能让测试快 100 倍？
