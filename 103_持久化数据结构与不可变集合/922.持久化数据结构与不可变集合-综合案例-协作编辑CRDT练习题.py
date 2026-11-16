# ===== 第922课：持久化数据结构与不可变集合-综合案例-协作编辑CRDT =====
# 知识点：
#   - CRDT（无冲突复制数据类型）：多副本并发编辑，合并后必然收敛
#   - 核心性质：交换律 + 结合律 + 幂等 → 合并顺序无关
#   - RGA 思路：每个字符带唯一 id + 插入位置引用（插在哪个元素之后）
#   - 删除 = 墓碑（tombstone）标记，永不物理删除 → 并发删/插可判定
#   - 并发插入同一位置的冲突：用 (site_id, seq) 做确定性打破
#   - 对比 OT（操作变换）：CRDT 无需中心服务器协调，离线友好
# 依赖：无（标准库）


class CRDTText:
    """基于 RGA 思想的协作文本。elements[id] = (字符, 前驱id, 墓碑)。"""

    def __init__(self, site_id):
        self.site_id = site_id
        self.seq = 0
        self.elements = {}                    # id=(site,seq) -> [字符, 前驱, 墓碑]

    def insert_after(self, after_id, ch):
        self.seq += 1
        eid = (self.site_id, self.seq)
        self.elements[eid] = [ch, after_id, False]
        return eid

    def insert_text(self, after_id, text):
        prev = after_id
        ids = []
        for ch in text:
            prev = self.insert_after(prev, ch)
            ids.append(prev)
        return ids

    def delete(self, eid):
        if eid in self.elements:
            self.elements[eid][2] = True      # 墓碑：标记删除

    def merge(self, remote_elements):
        """合并远端元素集合：并集 + 墓碑取或（交换/结合/幂等）。"""
        for eid, entry in remote_elements.items():
            if eid not in self.elements:
                self.elements[eid] = [entry[0], entry[1], entry[2]]
            else:
                self.elements[eid][2] = self.elements[eid][2] or entry[2]

    def elements_snapshot(self):
        return {eid: [e[0], e[1], e[2]] for eid, e in self.elements.items()}

    def text(self):
        """重建可见文本：按 after 链遍历，并发插入按 (site, seq) 定序。"""
        children = {}
        for eid, entry in self.elements.items():
            children.setdefault(entry[1], []).append(eid)
        for lst in children.values():
            lst.sort(key=lambda eid: (eid[0], eid[1]))   # 确定性打破并发
        out = []

        def walk(anchor):
            for eid in children.get(anchor, []):
                entry = self.elements[eid]
                if not entry[2]:
                    out.append(entry[0])
                walk(eid)                     # 墓碑的子树仍要遍历！

        walk(None)
        return "".join(out)

    def tombstones(self):
        return sum(1 for e in self.elements.values() if e[2])

    def stats(self):
        return {"元素": len(self.elements), "墓碑": self.tombstones()}


print("== 初始：两个站点同步（空文档）==")
site_a = CRDTText(site_id=1)
site_b = CRDTText(site_id=2)
print(f"  站点 A = {site_a.stats()}, 站点 B = {site_b.stats()}")

print("\n== 场景 1：并发插入同一位置 ==")
ids_a = site_a.insert_text(None, "hello")
ids_b = site_b.insert_text(None, "world")
print(f"  A 离线输入 'hello'（插在文档头），B 离线输入 'world'（也在头部）")
site_a.merge(site_b.elements_snapshot())
site_b.merge(site_a.elements_snapshot())
t_a, t_b = site_a.text(), site_b.text()
print(f"  合并后 A = {t_a!r}")
print(f"  合并后 B = {t_b!r}")
print(f"  两站收敛一致: {t_a == t_b}（并发插入按 site_id 定序，结果确定）")

print("\n== 场景 2：合并顺序无关性 ==")
site_c = CRDTText(site_id=3)
site_c.merge(site_b.elements_snapshot())
site_c.merge(site_a.elements_snapshot())      # 先 B 后 A
site_d = CRDTText(site_id=4)
site_d.merge(site_a.elements_snapshot())
site_d.merge(site_b.elements_snapshot())      # 先 A 后 B
print(f"  站点 C（先B后A）= {site_c.text()!r}")
print(f"  站点 D（先A后B）= {site_d.text()!r}")
print(f"  顺序无关: {site_c.text() == site_d.text()}（交换律保证）")

print("\n== 场景 3：并发删除与插入 ==")
target = ids_a[2]                              # 'l'（hello 的第二个 l）
site_a.delete(target)                          # A 删掉它
site_b.insert_text(target, "X")                # B 同时在被删字符后插入 X
site_a.merge(site_b.elements_snapshot())
site_b.merge(site_a.elements_snapshot())
print(f"  A 删除 'l'，B 在该位置后插入 'X' -> 合并后:")
print(f"  A = {site_a.text()!r}  B = {site_b.text()!r}  一致: {site_a.text() == site_b.text()}")
print("  规则：墓碑不阻挡其后代 —— 插在被删字符后面的 X 依然可见")
print(f"  A 墓碑数 = {site_a.tombstones()}, B 墓碑数 = {site_b.tombstones()}")

print("\n== 场景 4：三个人并发编辑 ==")
site_e = CRDTText(site_id=5)
site_a.insert_text(None, "A!")
site_b.insert_text(None, "B!")
site_e.insert_text(None, "E!")
merged = CRDTText(site_id=9)
merged.merge(site_a.elements_snapshot())
merged.merge(site_b.elements_snapshot())
merged.merge(site_e.elements_snapshot())
print(f"  三人分别在文档头输入 A!/B!/E! -> 合并 = {merged.text()!r}")
print("  定序 (site_id, seq)：site1 的 A! -> site2 的 B! -> site5 的 E!")

print("\n== 幂等性验证 ==")
before = site_a.text()
for _ in range(5):
    site_a.merge(site_b.elements_snapshot())   # 重复合并同一集合
print(f"  重复合并 5 次后文本不变: {site_a.text() == before}（幂等 ✓）")

print("\n== 与其他方案对比 ==")
print(f"  {'方案':<14}{'合并方式':<22}{'离线':<8}{'依赖'}")
for row in (("OT 操作变换", "中心服务器变换", "弱", "服务器"),
            ("CRDT", "状态自动合并", "强", "无（点对点）"),
            ("锁 + 轮询", "加锁串行", "无", "锁服务")):
    print(f"  {row[0]:<14}{row[1]:<22}{row[2]:<8}{row[3]}")

print("\n== CRDT 的代价 ==")
for line in (
    "  墓碑永不删除 → 元素集合只增不减，需要 GC（因果稳定后清理）",
    "  元数据（id/前驱）随字符走 → 内存是纯文本的数倍",
    "  定序规则决定「并发插入的相对顺序」—— 用户可见的怪异排序",
    "  生产实现：Yjs/Automerge/Redis Enterprise CRDB 都是这套思路",
):
    print("  -", line)

print("\n== 与向量时钟的联系 ==")
print("  GC（删除墓碑）需要知道『所有站点都见过这个删除』——")
print("  这正是 731 课向量时钟回答的问题：各站点的知识边界")

print("\n== 小结 ==")
for line in (
    "  CRDT = 数据结构 + 合并律（交换/结合/幂等）→ 收敛是数学保证",
    "  RGA：字符带 id 与前驱，插入链 + site 定序，删除用墓碑",
    "  不可变元素集合 + 纯函数合并 —— 与本章持久化思想一脉相承",
    "  协作编辑器、协同白板、分布式计数器都是 CRDT 的舞台",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「向量时钟」版本向量，给 CRDTText 加因果稳定的墓碑 GC。
# 2. 实现光标位置共享：把每个站点的光标也建模为 CRDT（锚定元素 id）。
# 3. 构造「并发插入同一字符后不同顺序」的用例，验证定序规则的稳定性。
# 4. 思考：为什么 OT 需要中心服务器而 CRDT 不需要？交换律/结合律/幂等
#    分别在合并的哪个环节发挥作用？
