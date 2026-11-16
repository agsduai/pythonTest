# ===== 第921课：持久化数据结构与不可变集合-函数式状态管理（reducer） =====
# 知识点：
#   - reducer 模式：状态只通过 reducer(state, action) -> new_state 变化
#   - reducer 必须是纯函数：同输入永远同输出、不碰外部 —— 可测试/可重放
#   - 不可变状态 + 持久化结构 → 每次派发都是一个快照（时间旅行免费）
#   - 事件重放：从初始状态按顺序应用动作日志 → 必然得到相同状态
#   - 与 515-522 事件溯源同源：动作日志是真相，状态只是投影
# 依赖：无（标准库）
import json


def initial_state():
    return {"todos": (), "next_id": 1, "filter": "all"}     # 全部不可变


def reducer(state, action):
    """纯函数：不修改 state，永远返回新 state。"""
    kind = action["type"]
    if kind == "ADD_TODO":
        todo = {"id": state["next_id"],
                "text": action["text"],
                "done": False}
        return {"todos": state["todos"] + (todo,),      # 元组拼接 = 持久化
                "next_id": state["next_id"] + 1,
                "filter": state["filter"]}
    if kind == "TOGGLE_TODO":
        new_todos = tuple(
            {**t, "done": not t["done"]} if t["id"] == action["id"] else t
            for t in state["todos"])
        return {"todos": new_todos, "next_id": state["next_id"],
                "filter": state["filter"]}
    if kind == "REMOVE_TODO":
        new_todos = tuple(t for t in state["todos"] if t["id"] != action["id"])
        return {"todos": new_todos, "next_id": state["next_id"],
                "filter": state["filter"]}
    if kind == "SET_FILTER":
        return {**state, "filter": action["value"]}
    if kind == "CLEAR_DONE":
        new_todos = tuple(t for t in state["todos"] if not t["done"])
        return {"todos": new_todos, "next_id": state["next_id"],
                "filter": state["filter"]}
    raise ValueError(f"未知动作 {kind}")


class Store:
    """不可变状态仓库：派发、订阅、撤销、重放。"""

    def __init__(self, reducer, state):
        self._reducer = reducer
        self._state = state
        self._history = [state]                # 每次派发后的快照
        self._actions = []                     # 动作日志（事件溯源）
        self._redo = []
        self._subscribers = []

    def dispatch(self, action):
        new_state = self._reducer(self._state, action)
        self._actions.append(action)
        self._history.append(new_state)
        self._redo.clear()
        self._state = new_state
        for fn in self._subscribers:
            fn(new_state)
        return new_state

    def subscribe(self, fn):
        self._subscribers.append(fn)

    def state(self):
        return self._state

    def undo(self):
        if len(self._history) > 1:
            self._redo.append(self._actions.pop())
            self._history.pop()
            self._state = self._history[-1]
        return self._state

    def redo(self):
        if self._redo:
            action = self._redo.pop()
            return self.dispatch(action)
        return self._state

    def replay(self):
        """从初始状态重放全部动作 —— 纯函数的必然结果。"""
        state = self._history[0]
        for action in self._actions:
            state = self._reducer(state, action)
        return state


def todo_view(state):
    """视图函数：由状态派生展示数据（不可变的只读投影）。"""
    visible = [t for t in state["todos"]
               if state["filter"] == "all"
               or (state["filter"] == "done" and t["done"])
               or (state["filter"] == "active" and not t["done"])]
    done_n = sum(1 for t in state["todos"] if t["done"])
    return {"显示": [f"[{'✓' if t['done'] else ' '}] {t['text']}" for t in visible],
            "统计": f"共 {len(state['todos'])} 项，完成 {done_n}"}


print("== 定义动作流 ==")
actions = [
    {"type": "ADD_TODO", "text": "写周报"},
    {"type": "ADD_TODO", "text": "review PR"},
    {"type": "ADD_TODO", "text": "单元测试"},
    {"type": "TOGGLE_TODO", "id": 2},
    {"type": "SET_FILTER", "value": "done"},
    {"type": "SET_FILTER", "value": "all"},
]
store = Store(reducer, initial_state())
store.subscribe(lambda s: print(f"    [订阅者] {todo_view(s)['统计']}"))

print("\n== 依次派发 ==")
for action in actions:
    print(f"  dispatch {action}")
    store.dispatch(action)
state = store.state()
view = todo_view(state)
print(f"  当前状态: {json.dumps(state, ensure_ascii=False)}")
print(f"  视图: {view['显示']}  {view['统计']}")

print("\n== 纯函数验证：同输入同输出 ==")
s = initial_state()
a1 = reducer(s, {"type": "ADD_TODO", "text": "X"})
a2 = reducer(s, {"type": "ADD_TODO", "text": "X"})
print(f"  同一状态派发同一动作两次结果相同: {a1 == a2}")
print(f"  原 state 未被修改: {s == initial_state()}")
print(f"  状态字典是独立对象: {a1 is not s}")

print("\n== 时间旅行 ==")
print(f"  undo -> {store.undo()}")
print(f"  视图: {todo_view(store.state())['显示']}")
print(f"  redo -> {store.redo()}")
print(f"  视图: {todo_view(store.state())['显示']}")
print(f"  跳到第 3 个快照: {todo_view(store._history[3])['显示']}")

print("\n== 事件重放：日志即真相 ==")
replayed = store.replay()
print(f"  重放 {len(store._actions)} 个动作后的状态 == 当前状态: {replayed == store.state()}")
print(f"  动作日志: {[a['type'] for a in store._actions]}")
print("  把日志持久化（如 JSONL，643 课），就能在崩溃后重放出全部状态")
print("  这正是事件溯源架构的核心：append-only 日志 + 纯函数投影")

print("\n== 与 MVU/Elm/Redux 的对应 ==")
for line in (
    "  dispatch(action) = Elm 的 update / Redux 的 store.dispatch",
    "  reducer(state, action) 纯函数 = 可测试、可重放、可时间旅行",
    "  不可变状态 = 915~920 课全部结构的用武之地",
    "  视图是状态的纯投影 —— UI 框架（React）的 render(state) 同构",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  reducer 把『状态如何变化』压缩成一个纯函数",
    "  动作日志 + 纯函数 = 重放、撤销、审计全部免费",
    "  不可变性是这套体系的前提：任何原地修改都会破坏重放",
    "  922 课：多人同时编辑 —— 用 CRDT 解决并发合并",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 给 Store 加「动作日志持久化」：写 JSONL 文件并在新 Store 中重放恢复。
# 2. 实现 reducer 组合：根 reducer 把动作分发给子 reducer（各自管理子状态）。
# 3. 加「中间件」：dispatch 前后打日志/统计动作耗时（装饰 dispatch）。
# 4. 思考：为什么 reducer 里禁止副作用？如果里面有网络请求会破坏哪些性质？
