# ===== 第254课：算法入门-二叉树与遍历 =====
# 知识点：
#   - 二叉树：每个节点最多两个孩子（left/right）
#   - 深度优先三种遍历：前序(根左右)、中序(左根右)、后序(左右根)
#   - 层序遍历：用队列逐层处理（复习第251课）
#   - 二叉搜索树 BST：左 < 根 < 右 → 中序遍历结果天然有序

from collections import deque


class TreeNode:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None


def preorder(node, out):        # 根 → 左 → 右
    if node:
        out.append(node.value)
        preorder(node.left, out)
        preorder(node.right, out)


def inorder(node, out):         # 左 → 根 → 右
    if node:
        inorder(node.left, out)
        out.append(node.value)
        inorder(node.right, out)


def level_order(root):
    """层序遍历：队列 + 逐层出队。"""
    result, q = [], deque([root] if root else [])
    while q:
        node = q.popleft()
        result.append(node.value)
        if node.left:
            q.append(node.left)
        if node.right:
            q.append(node.right)
    return result


# 构造一棵树：
#        50
#       /  \
#     30    70
#    / \    / \
#  20  40  60  80
root = TreeNode(50)
root.left, root.right = TreeNode(30), TreeNode(70)
root.left.left, root.left.right = TreeNode(20), TreeNode(40)
root.right.left, root.right.right = TreeNode(60), TreeNode(80)

out = []
preorder(root, out)
print("前序：", out)
out = []
inorder(root, out)
print("中序：", out)
print("层序：", level_order(root))


# 二叉搜索树：插入与查找
def bst_insert(node, value):
    if node is None:
        return TreeNode(value)
    if value < node.value:
        node.left = bst_insert(node.left, value)
    else:
        node.right = bst_insert(node.right, value)
    return node


def bst_search(node, value, depth=1):
    if node is None:
        return None, depth
    if node.value == value:
        return node, depth
    child = node.left if value < node.value else node.right
    return bst_search(child, value, depth + 1)


bst = None
for x in (50, 30, 70, 20, 40, 60, 80):
    bst = bst_insert(bst, x)

out = []
inorder(bst, out)
print("BST 中序遍历（自动有序）：", out)

found, depth = bst_search(bst, 60)
print("查找 60，比较次数：", depth)
_, depth = bst_search(bst, 99)
print("查找 99（不存在），走到深度：", depth)

# ===== 练习题 =====
# 1. 实现后序遍历 postorder，验证输出。
# 2. 编写 tree_height(root)：计算树的高度（递归取左右子树较大值+1）。
# 3. 依次插入 10,20,30,40,50 构造 BST，画出形状，解释什么叫“退化成链表”。
# 4. 思考：BST 查找和第247课的二分查找有什么相似之处？
