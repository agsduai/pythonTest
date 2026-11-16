# ===== 第920课：持久化数据结构与不可变集合-时间旅行与版本diff =====
# 知识点：
#   - 快照 O(1) → 撤销/重做/跳转任意版本都是「引用切换」
#   - 版本 diff：持久化树的中序对比给出精确变更集
#   - 时间旅行调试：回到任意历史状态重放后续操作
#   - 内存账本：版本数 × 路径复制成本，远小于全量快照
#   - 与 515-522 事件溯源的关系：事件溯源存「动作」，持久化结构存「状态」
# 依赖：无（标准库）


def height(node):
    return node[4] if node is not None else 0


def mk(key, value, left, right):
    return (key, value, left, right,
            1 + max(height(left), height(right)))


def balance(key, value, left, right):
    hl, hr = height(left), height(right)
    if hl - hr > 1:
        if height(left[2]) >= height(left[3]):
            return mk(left[0], left[1], left[2],
                      mk(key, value, left[3], right))
        lchild = left[3]
        return mk(lchild[0], lchild[1],
                  mk(left[0], left[1], left[2], lchild[2]),
                  mk(key, value, lchild[3], right))
    if hr - hl > 1:
        if height(right[3]) >= height(right[2]):
            return mk(right[0], right[1],
                      mk(key, value, left, right[2]), right[3])
        rchild = right[2]
        return mk(rchild[0], rchild[1],
                  mk(key, value, left, rchild[2]),
                  mk(right[0], right[1], rchild[3], right[3]))
    return mk(key, value, left, right)


def insert(node, key, value):
    if node is None:
        return mk(key, value, None, None)
    k, v, l, r, _ = node
    if key == k:
        return mk(key, value, l, r)
    if key < k:
        return balance(k, v, insert(l, key, value), r)
    return balance(k, v, l, insert(r, key, value))


def get(node, key, default=None):
    while node is not None:
        k, v, l, r, _ = node
        if key == k:
            return v
        node = l if key < k else r
    return default


def inorder(node, out=None):
    if out is None:
        out = []
    if node is not None:
        inorder(node[2], out)
        out.append((node[0], node[1]))
        inorder(node[3], out)
    return out


def collect_ids(node, seen=None):
    if seen is None:
        seen = set()
    if node is None or id(node) in seen:
        return seen
    seen.add(id(node))
    collect_ids(node[2], seen)
    collect_ids(node[3], seen)
    return seen


def diff(node_a, node_b):
    a = dict(inorder(node_a))
    b = dict(inorder(node_b))
    return (sorted(set(b) - set(a)), sorted(set(a) - set(b)),
            sorted(k for k in set(a) & set(b) if a[k] != b[k]))


class TimeTravelDoc:
    """持久化文档：每个版本是一棵持久化 AVL 的根。"""

    def __init__(self):
        self.versions = [None]           # 版本 0 = 空文档
        self.labels = ["初始"]
        self.cursor = 0                  # 当前所在版本

    def edit(self, key, value, label):
        new_root = insert(self.versions[self.cursor], key, value)
        # 裁掉游标之后的「被放弃的未来」（git 语义），也可保留成分支
        self.versions = self.versions[:self.cursor + 1]
        self.labels = self.labels[:self.cursor + 1]
        self.versions.append(new_root)
        self.labels.append(label)
        self.cursor = len(self.versions) - 1

    def undo(self):
        if self.cursor > 0:
            self.cursor -= 1
        return self.labels[self.cursor]

    def redo(self):
        if self.cursor < len(self.versions) - 1:
            self.cursor += 1
        return self.labels[self.cursor]

    def jump(self, version_index):
        self.cursor = max(0, min(version_index, len(self.versions) - 1))
        return self.labels[self.cursor]

    def state(self):
        return {k: v for k, v in inorder(self.versions[self.cursor])}

    def current_label(self):
        return self.labels[self.cursor]


print("== 编辑时间线 ==")
doc = TimeTravelDoc()
edits = [("标题", "我的笔记", "写入标题"),
         ("作者", "小明", "署名"),
         ("第一章", "引言内容", "写第一章"),
         ("标题", "我的学习笔记", "改标题"),
         ("第二章", "正文内容", "写第二章")]
for key, value, label in edits:
    doc.edit(key, value, label)
    print(f"  [{label}] 版本 {doc.cursor}: {doc.state()}")

print("\n== 撤销两步 ==")
print(f"  undo -> {doc.undo()}: {doc.state()}")
print(f"  undo -> {doc.undo()}: {doc.state()}")

print("\n== 重做一步 ==")
print(f"  redo -> {doc.redo()}: {doc.state()}")

print("\n== 跳转任意版本 ==")
print(f"  jump(1) -> {doc.jump(1)}: {doc.state()}")
print(f"  jump(3) -> {doc.jump(3)}: {doc.state()}")
print(f"  当前版本 = {doc.current_label()}（版本 {doc.cursor}）")

print("\n== 版本 diff ==")
for i, j in ((0, 4), (1, 4), (2, 5)):
    a, b = doc.versions[i], doc.versions[j]
    added, removed, changed = diff(a, b)
    print(f"  v{i}({doc.labels[i]}) -> v{j}({doc.labels[j]}): "
          f"+{added} -{removed} ~{changed}")

print("\n== 从历史分叉 ==")
fork_point = 2
old_root = doc.versions[fork_point]
branch = insert(old_root, "番外", "分叉实验")
print(f"  从 v{fork_point}({doc.labels[fork_point]}) 分叉出『番外』版本:")
print(f"  分叉状态: {dict(inorder(branch))}")
print(f"  主线最新状态不受影响: {doc.state()}")

print("\n== 内存账本 ==")
all_ids = set()
for v in doc.versions:
    all_ids |= collect_ids(v)
total_nodes = sum(len(collect_ids(v)) for v in doc.versions)
print(f"  {len(doc.versions)} 个版本，各版本节点数合计 {total_nodes}")
print(f"  实际占用唯一节点 = {len(all_ids)}（结构共享率 "
      f"{1 - len(all_ids) / max(total_nodes, 1):.1%}）")
print("  全量快照需要 5 × 节点数；共享让历史几乎免费")

print("\n== 时间旅行调试的工程形态 ==")
for line in (
    "  Redux DevTools：每个 action 存快照，可跳回任意时刻",
    "  Elm/Immutable.js：持久化结构让 undo 是免费的",
    "  数据库快照隔离（727 课 MVCC）：同一思想在存储层的实现",
    "  事件溯源（515 课）：存动作序列 vs 本课存状态版本，二者可结合",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  快照 O(1) 让『历史』从功能变成基础设施",
    "  跳转/diff/分叉/重放四件套构成时间旅行调试的全部原语",
    "  放弃的未来可以保留成分支 —— git 的 commit 图就是持久化树",
    "  921 课：把持久化结构接到应用状态管理上（reducer 模式）",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「分支保留」版 TimeTravelDoc：undo 后再 edit 不丢弃旧未来，而是
#    创建分支，支持 branch 列表与切换。
# 2. 实现「按标签跳转」：named snapshot（如 jump_to("初稿")）。
# 3. 统计 1000 次编辑的历史内存占用，对比「每次全量 dict.copy」方案。
# 4. 思考：时间旅行调试为什么在不可变状态的应用里几乎是零成本的？
