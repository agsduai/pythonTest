# ===== 第495课：动态规划专题-树形DP =====
# 知识点：
#   - 树形 DP：在树上做递归，子节点结果向父节点汇总
#   - 经典题 1：二叉树最大路径和（路径可以不经过根）
#     - 递归返回“以当前节点为端点向下走的最大收益”
#     - 全局答案在“左收益 + 当前值 + 右收益”处更新
#   - 经典题 2：打家劫舍 III（相邻节点不能同时选）
#     - 每个节点返回 (选它的最优, 不选它的最优) 两个状态
#   - 与第254课二叉树遍历、第494课区间DP的“状态设计”思路一致
# 依赖：无


class Node:
    def __init__(self, val, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


# ---------------- 1. 二叉树最大路径和 ----------------
def max_path_sum(root: Node) -> int:
    best = float("-inf")

    def gain(node: Node) -> int:
        """以 node 为起点向下走的最大收益（负数则不走）。"""
        nonlocal best
        if node is None:
            return 0
        left_gain = max(gain(node.left), 0)
        right_gain = max(gain(node.right), 0)
        # 路径在 node 处“拐弯”：左 + 当前 + 右
        best = max(best, node.val + left_gain + right_gain)
        # 返回给父节点：只能选一边往下走
        return node.val + max(left_gain, right_gain)

    gain(root)
    return best


# 树：[-10, 9, 20, None, None, 15, 7]
root = Node(-10,
            Node(9),
            Node(20, Node(15), Node(7)))
print("== 二叉树最大路径和 ==")
print("  树结构：-10 / \\ 9 20 / \\ 15 7")
print("  最大路径和：", max_path_sum(root), "（15 → 20 → 7 = 42）")

# 全负数：至少选一个节点
neg = Node(-3, Node(-2), Node(-5))
print("  全负数树：", max_path_sum(neg), "（不能选空路径，至少选 -2）")

# ---------------- 2. 打家劫舍 III ----------------
def rob_tree(root: Node) -> int:
    """相邻（父子）节点不能同时选，返回最大金额。"""
    def dfs(node: Node):
        """返回 (选 node 的最优, 不选 node 的最优)。"""
        if node is None:
            return 0, 0
        left_rob, left_skip = dfs(node.left)
        right_rob, right_skip = dfs(node.right)

        rob_current = node.val + left_skip + right_skip     # 选它 → 子节点必须不选
        skip_current = max(left_rob, left_skip) + max(right_rob, right_skip)
        return rob_current, skip_current

    return max(dfs(root))


house = Node(3,
             Node(2, None, Node(3)),
             Node(3, None, Node(1)))
print("\n== 打家劫舍 III ==")
print("  树结构：3 / \\ 2 3 \\ \\ 3 1")
print("  最大金额：", rob_tree(house), "（选 3 + 3 + 1 = 7）")

# ---------------- 3. 树形 DP 模板 ----------------
print("\n== 树形 DP 通用模板 ==")
print("  def dfs(node):")
print("      left = dfs(node.left)")
print("      right = dfs(node.right)")
print("      # 1) 用 left/right 更新全局答案（路径在 node 拐弯）")
print("      # 2) 返回给父节点的单边最优值")
print("  dfs(root)")

print("\n== 状态设计要点 ==")
for item in [
    "返回值是“给父节点用”的信息，不一定等于最终答案",
    "需要多个状态时返回元组（选/不选、rob/skip）",
    "全局答案用 nonlocal/类属性在递归中更新",
    "树很深时注意递归深度限制（第233课）",
]:
    print("  -", item)

# ---------------- 4. 与分治的区别 ----------------
print("\n== 与分治的区别 ==")
print("  分治：子问题互不重叠，合并即可（归并排序）")
print("  树形 DP：子问题结果要按“状态”组合，可能有全局最优在中间拐弯")
print("  相同点：都是递归向下、汇总向上")

# ===== 练习题 =====
# 1. 给 max_path_sum 增加“返回路径本身”的能力。
# 2. 计算二叉树的“最大同值路径”（相邻节点值相同）。
# 3. 给打家劫舍 III 增加“不能选祖父-孙子同时选”的变体。
# 4. 思考：为什么 max_path_sum 返回给父节点时只能选一边？
