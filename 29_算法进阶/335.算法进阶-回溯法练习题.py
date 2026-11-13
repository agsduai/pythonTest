# ===== 第335课：算法进阶-回溯法 =====
# 知识点：
#   - 回溯 = 试错搜索：做选择 → 递归深入 → 撤销选择换下一条路
#   - 三要素：路径（已做的选择）、选择列表、结束条件
#   - 经典：全排列、子集、N 皇后
#   - 与第249课分治的区别：回溯是“搜索所有可能”，剪枝决定生死
# 依赖：无

# ---- 全排列：回溯模板的最小样例 ----
def permutations(nums):
    result, path = [], []

    def backtrack(remaining):
        if not remaining:                    # 结束条件
            result.append(path[:])           # 注意拷贝！
            return
        for i, x in enumerate(remaining):
            path.append(x)                   # 做选择
            backtrack(remaining[:i] + remaining[i + 1:])
            path.pop()                       # 撤销选择 ← 回溯的灵魂

    backtrack(nums)
    return result


print("全排列：", permutations([1, 2, 3]))

# ---- 子集 ----
def subsets(nums):
    result = []

    def backtrack(start, path):
        result.append(path[:])
        for i in range(start, len(nums)):
            path.append(nums[i])
            backtrack(i + 1, path)
            path.pop()

    backtrack(0, [])
    return result


print("所有子集：", subsets([1, 2, 3]))

# ---- N 皇后（4 皇后，共 2 个解）----
def solve_n_queens(n=4):
    solutions = []
    cols, diag1, diag2, board = set(), set(), set(), []

    def place(row):
        if row == n:
            solutions.append(board[:])
            return
        for col in range(n):
            if col in cols or (row - col) in diag1 or (row + col) in diag2:
                continue                     # 剪枝：同列/对角线冲突
            cols.add(col); diag1.add(row - col); diag2.add(row + col)
            board.append(col)
            place(row + 1)
            board.pop()
            cols.remove(col); diag1.remove(row - col); diag2.remove(row + col)

    place(0)
    return solutions


solutions = solve_n_queens(4)
print(f"4 皇后共 {len(solutions)} 个解，其中一个解（列号）：", solutions[0])

# ===== 练习题 =====
# 1. 全排列加剪枝：只输出“首位小于末位”的排列。
# 2. 把 N 皇后改成打印棋盘图案（Q 与 .）。
# 3. 思考：回溯和穷举的区别是什么？剪枝省掉了哪部分计算？
