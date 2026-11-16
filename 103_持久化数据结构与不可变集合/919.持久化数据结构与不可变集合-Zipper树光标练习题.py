# ===== 第919课：持久化数据结构与不可变集合-Zipper树光标 =====
# 知识点：
#   - Zipper = 「聚焦 + 上下文」：数据结构的光标，可上/下/左右移动
#   - 上下文记录「怎么走到这里」：每个方向 + 兄弟子树 + 父值
#   - 修改只影响聚焦点；top() 沿上下文重建出整棵新树
#   - 与路径复制等价，但把「在哪编辑」显式化 —— 编辑器/焦点系统的抽象
#   - 类型论视角：zipper 是数据类型的「导数」（单孔上下文）
# 依赖：无（标准库）


class Zipper:
    """二叉树的 zipper。focus = (value, left, right) 或 None。
    context: 元组，每项 ("L"/"R", 父值, 兄弟子树)。"""

    def __init__(self, focus, context=()):
        self.focus = focus
        self.context = context

    def value(self):
        return self.focus[0] if self.focus is not None else None

    def go_down_left(self):
        if self.focus is None or self.focus[1] is None:
            raise ValueError("没有左子节点")
        value, left, right = self.focus
        return Zipper(left, self.context + (("L", value, right),))

    def go_down_right(self):
        if self.focus is None or self.focus[2] is None:
            raise ValueError("没有右子节点")
        value, left, right = self.focus
        return Zipper(right, self.context + (("R", value, left),))

    def go_up(self):
        if not self.context:
            raise ValueError("已经在根节点")
        side, parent_value, sibling = self.context[-1]
        if side == "L":
            parent = (parent_value, self.focus, sibling)
        else:
            parent = (parent_value, sibling, self.focus)
        return Zipper(parent, self.context[:-1])

    def go_top(self):
        z = self
        while z.context:
            z = z.go_up()
        return z

    def set_value(self, v):
        if self.focus is None:
            raise ValueError("空位置不可赋值")
        _, left, right = self.focus
        return Zipper((v, left, right), self.context)

    def set_focus(self, new_subtree):
        return Zipper(new_subtree, self.context)

    def path(self):
        return "/".join(side for side, _, _ in self.context) or "root"


def tree_lines(node, indent=0):
    if node is None:
        return ["  " * indent + "·"]
    v, l, r = node
    return ([f"{'  ' * indent}{v}"]
            + tree_lines(l, indent + 1) + tree_lines(r, indent + 1))


def render_tree(node):
    return "\n".join(tree_lines(node))


print("== 示例树 ==")
tree = (1,
        (2, (4, None, None), (5, None, None)),
        (3, (6, None, None), (7, None, None)))
print(render_tree(tree))

print("\n== 导航 ==")
z = Zipper(tree)
print(f"  起点: {z.path()}, value = {z.value()}")
z = z.go_down_left()
print(f"  go_down_left -> {z.path()}, value = {z.value()}")
z = z.go_down_right()
print(f"  go_down_right -> {z.path()}, value = {z.value()}（聚焦到节点 5）")
z2 = z.go_up().go_up().go_down_right().go_down_left()
print(f"  另一条路径: {z2.path()}, value = {z2.value()}（聚焦到节点 6）")

print("\n== 局部修改 ==")
z_edit = z2.set_value(66)
new_tree = z_edit.go_top().focus
print(f"  把聚焦的 6 改成 66 后整棵树:")
print(render_tree(new_tree))
old_values = []


def collect(node):
    if node is not None:
        collect(node[1])
        old_values.append(node[0])
        collect(node[2])


collect(tree)
print(f"  原树仍含 6（未被改动）: {6 in old_values}")

print("\n== 同一聚焦点的两份编辑 ==")
edit_a = z2.set_value(66).go_top().focus          # 6 -> 66
edit_b = z2.go_up().set_value(33).go_top().focus  # 3 -> 33
print("  从同一光标位置分叉两次编辑（6→66 与 3→33）:")
print("  -- 编辑 A --")
print(render_tree(edit_a))
print("  -- 编辑 B --")
print(render_tree(edit_b))
print("  两个未来并存 —— 与 917 课的版本分叉同构，但粒度是『光标位置』")

print("\n== 替换整棵子树 ==")
z3 = Zipper(tree).go_down_right()
z3b = z3.set_focus((30, (31, None, None), (32, None, None)))
print("  把子树 3 整体替换为 30(31,32):")
print(render_tree(z3b.go_top().focus))

print("\n== 错误导航 ==")
try:
    Zipper(tree).go_up()
except ValueError as exc:
    print(f"  根节点 go_up: {exc}")
try:
    z_down = Zipper(tree).go_down_left()
    z_down.go_down_left().go_down_left()
except ValueError as exc:
    print(f"  越过叶子: {exc}")

print("\n== 小结 ==")
for line in (
    "  zipper = 聚焦 + 可逆的上下文栈：移动即构造，返回即重建",
    "  局部修改与 917 课路径复制等价，但抽象成『光标』更好用",
    "  编辑器光标、文件系统路径、GUI 焦点系统都是 zipper 思想",
    "  类型论彩蛋：zipper 是数据类型的『导数』—— 有孔的版本",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现列表的 zipper（光标左右移动、插入、删除），做一个行内编辑器演示。
# 2. 实现 n 叉树的 zipper：context 记录 (父值, 左兄弟列表, 右兄弟列表)。
# 3. 用 zipper 实现「深度优先搜索的状态回退」（回溯时 go_up 即可）。
# 4. 思考：为什么 zipper 在纯函数式语言里能替代「可变指针 + 父指针」？
#    双向导航靠什么数据实现？
