# ===== 第395课：设计模式进阶-组合模式 =====
# 知识点：
#   - 组合：把“单个对象”和“对象容器”统一成同一种接口
#   - 客户端对叶子节点和目录节点一视同仁：都调用 size()/show()
#   - 天然递归：目录的 size = 所有子项 size 之和
#   - 场景：文件系统、菜单树、组织架构、UI 控件树、表达式树
from abc import ABC, abstractmethod


class Node(ABC):

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def size(self) -> int: ...

    @abstractmethod
    def show(self, indent: int = 0) -> str: ...


class File(Node):
    """叶子节点：没有子项。"""

    def __init__(self, name: str, size: int):
        super().__init__(name)
        self._size = size

    def size(self) -> int:
        return self._size

    def show(self, indent: int = 0) -> str:
        return f"{'  ' * indent}📄 {self.name} ({self._size}KB)"


class Dir(Node):
    """容器节点：可以装文件，也可以装子目录。"""

    def __init__(self, name: str):
        super().__init__(name)
        self.children: list[Node] = []

    def add(self, node: Node) -> "Dir":
        self.children.append(node)
        return self                         # 支持链式添加

    def size(self) -> int:
        return sum(child.size() for child in self.children)

    def show(self, indent: int = 0) -> str:
        lines = [f"{'  ' * indent}📁 {self.name}/ ({self.size()}KB)"]
        for child in self.children:
            lines.append(child.show(indent + 1))
        return "\n".join(lines)

    def find(self, keyword: str) -> list[Node]:
        """统一递归查找：文件看自己名字，目录先看自己再下钻。"""
        found = []
        if keyword in self.name:
            found.append(self)
        for child in self.children:
            if isinstance(child, Dir):
                found.extend(child.find(keyword))
            elif keyword in child.name:
                found.append(child)
        return found


# ---- 组装一棵目录树 ----
root = Dir("项目")
root.add(File("README.md", 12)).add(
    Dir("src").add(File("app.py", 34)).add(File("utils.py", 18))
).add(
    Dir("tests").add(File("test_app.py", 26))
).add(File("requirements.txt", 3))

print("== 目录树 ==")
print(root.show())
print("\n总大小：", root.size(), "KB")

# ---- 统一接口：不关心当前是文件还是目录 ----
print("\n== 遍历所有节点（一视同仁）==")
stack = [root]
while stack:
    node = stack.pop()
    print(f"  {type(node).__name__:5s} {node.name:15s} {node.size():3d}KB")
    if isinstance(node, Dir):
        stack.extend(node.children)

# ---- 递归查找 ----
print("\n== 查找包含 'test' 的节点 ==")
for node in root.find("test"):
    print("  ", node.show().strip())

# ---- 目录也可以只统计某一层 ----
print("\n== 各模块占用 ==")
for child in root.children:
    if isinstance(child, Dir):
        print(f"  {child.name}: {child.size()}KB")

# ===== 练习题 =====
# 1. 给 Node 增加 count_files()：文件返回 1，目录返回子树内文件总数。
# 2. 增加“删除节点”方法（注意父目录如何找到它）。
# 3. 用组合模式描述“表达式树”：数字是叶子，加减乘除是容器，实现 evaluate()。
# 4. 思考：组合模式与第254课二叉树递归遍历有什么相通之处？
