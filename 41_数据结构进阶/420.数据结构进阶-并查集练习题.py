# ===== 第420课：数据结构进阶-并查集 =====
# 知识点：
#   - 并查集（Union-Find）：维护“分组”，支持合并与查询是否同组
#   - find(x)：找根节点；带路径压缩后接近 O(1)
#   - union(a,b)：按秩/大小合并，避免树退化成链表
#   - 应用：社交网络连通块、网络是否连通、Kruskal 最小生成树、账户合并
#   - 与第332课 BFS 的区别：并查集适合“动态加边 + 反复查询”，BFS 适合一次遍历


class UnionFind:

    def __init__(self, n: int | None = None):
        self.parent: dict = {}
        self.size: dict = {}
        if n is not None:
            for i in range(n):
                self.parent[i] = i
                self.size[i] = 1

    def add(self, x):
        if x not in self.parent:
            self.parent[x] = x
            self.size[x] = 1

    def find(self, x):
        self.add(x)
        root = x
        while self.parent[root] != root:      # 先找根
            root = self.parent[root]
        while self.parent[x] != root:         # 路径压缩：把沿途节点直接挂到根
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b) -> bool:
        """合并成功返回 True；本来就在同一组返回 False。"""
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:     # 小树挂到大树
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        return True

    def connected(self, a, b) -> bool:
        return self.find(a) == self.find(b)

    def group_count(self) -> int:
        return len({self.find(x) for x in self.parent})


# ---- 社交网络：谁和谁在同一个圈子 ----
uf = UnionFind()
edges = [
    ("小明", "小红"), ("小红", "小刚"),        # 圈子 1
    ("小丽", "小美"),                          # 圈子 2
    ("小强", "小明"),                          # 小强并入圈子 1
]
for a, b in edges:
    merged = uf.union(a, b)
    print(f"  合并 {a}-{b}：{'成功' if merged else '已同组'}")

print("\n圈子数量：", uf.group_count())
pairs = [("小明", "小强"), ("小明", "小丽"), ("小丽", "小美")]
for a, b in pairs:
    print(f"  {a} 与 {b} 同圈：{uf.connected(a, b)}")

# ---- 加边检测环：Kruskal 的前置能力 ----
print("\n== 环检测 ==")
uf2 = UnionFind(n=5)
graph_edges = [(0, 1), (1, 2), (2, 3), (3, 0), (3, 4)]
for a, b in graph_edges:
    if not uf2.union(a, b):
        print(f"  加入边 {a}-{b} 会形成环")

# ---- 账户合并：邮箱相同即同一人（并查集经典题）----
print("\n== 账户合并 ==")
accounts = [
    ["张三", "a@x.com", "b@x.com"],
    ["张三", "b@x.com", "c@x.com"],
    ["李四", "d@x.com"],
]
email_owner = {}
uf3 = UnionFind()
for i, acc in enumerate(accounts):
    uf3.add(i)
    for email in acc[1:]:
        if email in email_owner:
            uf3.union(i, email_owner[email])
        else:
            email_owner[email] = i

groups = {}
for i, acc in enumerate(accounts):
    groups.setdefault(uf3.find(i), set()).update(acc[1:])
print("  合并后的账户：")
for emails in groups.values():
    print("   ", sorted(emails))

# ===== 练习题 =====
# 1. 实现“省份数量”题：给定邻接矩阵，用并查集数连通块。
# 2. 用并查集实现 Kruskal 最小生成树（边先按权重排序）。
# 3. 给 UnionFind 增加 largest_group_size()。
# 4. 思考：为什么路径压缩后 find 接近 O(1)？最坏还能到多少？
