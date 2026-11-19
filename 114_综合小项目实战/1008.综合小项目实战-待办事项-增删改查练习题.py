# ===== 第1008课：综合小项目实战-待办事项——增删改查 =====
# 知识点：
#   - 列表存待办事项：每项 {id, text, done} —— id 用递增编号
#   - 状态管理：done 字段标记完成/未完成
#   - 增删改查四个基本操作（CRUD）
#   - 数据持久化：JSON 文件保存
# 依赖：无（标准库）
import json
import os

TODO_FILE = "todos.json"


def load_todos():
    if not os.path.exists(TODO_FILE):
        return []
    with open(TODO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_todos(todos):
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def get_next_id(todos):
    """获取下一个可用 id（当前最大 id + 1）。"""
    if not todos:
        return 1
    return max(t["id"] for t in todos) + 1


def add_todo(todos, text):
    """添加待办事项。"""
    todo = {"id": get_next_id(todos), "text": text, "done": False}
    todos.append(todo)
    save_todos(todos)
    return todo


def toggle_todo(todos, todo_id):
    """切换完成/未完成状态。返回 (是否成功, 新状态)。"""
    for todo in todos:
        if todo["id"] == todo_id:
            todo["done"] = not todo["done"]
            save_todos(todos)
            return True, todo["done"]
    return False, None


def remove_todo(todos, todo_id):
    """删除待办事项。"""
    original_len = len(todos)
    todos[:] = [t for t in todos if t["id"] != todo_id]
    if len(todos) < original_len:
        save_todos(todos)
        return True
    return False


def show_todos(todos, show_all=True):
    """显示待办事项。"""
    if not todos:
        print("  没有待办事项")
        return
    for todo in todos:
        if not show_all and todo["done"]:
            continue
        status = "✓" if todo["done"] else " "
        print(f"  [{status}] #{todo['id']} {todo['text']}")
    done_count = sum(1 for t in todos if t["done"])
    print(f"  共 {len(todos)} 项，已完成 {done_count} 项")


# 使用演示
todos = load_todos()
print("== 待办事项管理 ==")

print("\n== 添加 ==")
todo1 = add_todo(todos, "买牛奶")
todo2 = add_todo(todos, "写作业")
todo3 = add_todo(todos, "锻炼身体")
todo4 = add_todo(todos, "复习 Python")
show_todos(todos)

print("\n== 完成第 1 项 ==")
toggle_todo(todos, 1)
show_todos(todos)

print("\n== 只看未完成的 ==")
show_todos(todos, show_all=False)

print("\n== 删除第 3 项 ==")
remove_todo(todos, 3)
show_todos(todos)

print("\n== 尝试删除不存在的 ==")
result = remove_todo(todos, 99)
print(f"  删除 id=99: {'成功' if result else '不存在，无法删除'}")

# ===== 练习题 =====
# 1. 实现 clear_done(todos)：删除所有已完成的待办事项。
# 2. 实现按状态过滤：只显示已完成或只显示未完成。
# 3. 实现编辑功能：修改待办事项的文字内容。
# 4. 思考：为什么用递增 id 而不用列表下标作为标识？下标会因删除而变化。
