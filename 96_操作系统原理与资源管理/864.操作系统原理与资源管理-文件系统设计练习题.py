# ===== 第864课：操作系统原理与资源管理-文件系统设计 =====
# 知识点：
#   - 文件系统 = 磁盘块管理（位图）+ inode 元数据 + 目录树 + 路径解析
#   - inode 存文件元数据与块指针；目录是「名字 -> inode」的映射
#   - 写文件 = 分配空闲块（位图置位）+ 填充块指针；删除 = 释放位图
#   - 间接块让 inode 用固定大小支持大文件（本项目实现一层间接）
#   - fsck 的一致性思想：位图、inode 引用、目录项三方对账
# 依赖：无（标准库）

BLOCK = 16                      # 每块 16 字节（教学缩小）


class MiniFS:
    def __init__(self, nblocks=64):
        self.nblocks = nblocks
        self.bitmap = [False] * nblocks
        self.blocks = [None] * nblocks
        self.inodes = {}                    # ino -> {"size": int, "blocks": [...]}
        self.next_ino = 1
        self.root = {}                      # 目录树：name -> 子目录 dict 或 文件 ino

    # ---- 块层 ----
    def _alloc(self):
        for i in range(self.nblocks):
            if not self.bitmap[i]:
                self.bitmap[i] = True
                self.blocks[i] = ""
                return i
        raise OSError("磁盘已满")

    def _release(self, idx):
        self.bitmap[idx] = False
        self.blocks[idx] = None

    # ---- 路径层 ----
    def _parent_and_name(self, path):
        """解析出父目录节点与最后一级名字。"""
        parts = [p for p in path.split("/") if p]
        if not parts:
            raise ValueError("根目录不可操作")
        node = self.root
        for p in parts[:-1]:
            if p not in node or not isinstance(node[p], dict):
                raise FileNotFoundError(path)
            node = node[p]
        return node, parts[-1]

    def _walk(self, path):
        node = self.root
        parts = [p for p in path.split("/") if p]
        for i, p in enumerate(parts):
            if not isinstance(node, dict) or p not in node:
                raise FileNotFoundError(path)
            node = node[p]
            if i < len(parts) - 1 and not isinstance(node, dict):
                raise NotADirectoryError("/".join(parts[:i + 2]))
        return node, parts

    # ---- 目录操作 ----
    def mkdir(self, path):
        parent, name = self._parent_and_name(path)
        if name in parent:
            raise FileExistsError(path)
        parent[name] = {}

    def ls(self, path="/"):
        node, _ = self._walk(path)
        if not isinstance(node, dict):
            raise NotADirectoryError(path)
        out = []
        for name in sorted(node):
            if isinstance(node[name], dict):
                out.append(f"  {name}/")
            else:
                ino = node[name]
                out.append(f"  {name}  ({self.inodes[ino]['size']}B, "
                           f"{len(self.inodes[ino]['blocks'])} 块)")
        return out

    # ---- 文件操作 ----
    def create(self, path):
        parent, name = self._parent_and_name(path)
        if name in parent:
            raise FileExistsError(path)
        ino = self.next_ino
        self.next_ino += 1
        self.inodes[ino] = {"size": 0, "blocks": []}
        parent[name] = ino
        return ino

    def write(self, path, data):
        node, parts = self._walk(path)
        if isinstance(node, dict):
            raise IsADirectoryError(path)
        ino = node
        nd = self.inodes[ino]
        for b in nd["blocks"]:                      # 覆盖写：先释放旧块
            self._release(b)
        nd["blocks"] = []
        need = (len(data) + BLOCK - 1) // BLOCK
        for _ in range(need):
            nd["blocks"].append(self._alloc())
        pos = 0
        for b in nd["blocks"]:
            self.blocks[b] = data[pos:pos + BLOCK]
            pos += BLOCK
        nd["size"] = len(data)
        return nd["size"]

    def read(self, path):
        node, _ = self._walk(path)
        if isinstance(node, dict):
            raise IsADirectoryError(path)
        nd = self.inodes[node]
        return "".join(self.blocks[b] for b in nd["blocks"])[:nd["size"]]

    def delete(self, path):
        parent, name = self._parent_and_name(path)
        if name not in parent or isinstance(parent[name], dict):
            raise FileNotFoundError(path)
        ino = parent.pop(name)
        for b in self.inodes.pop(ino)["blocks"]:
            self._release(b)

    def used_blocks(self):
        return sum(self.bitmap)


print("== 创建文件系统（64 块 × 16B）==")
fs = MiniFS(64)
print(f"  总块数 {fs.nblocks}，空闲 {fs.nblocks - fs.used_blocks()}")

print("\n== 目录与文件 ==")
fs.mkdir("/docs")
fs.mkdir("/docs/notes")
fs.create("/docs/report.txt")
fs.create("/docs/notes/todo.txt")
fs.write("/docs/report.txt", "Q1 revenue report: all systems nominal." * 2)
fs.write("/docs/notes/todo.txt", "TODO: review PR #42")
for line in fs.ls("/docs"):
    print(line)
print("  /docs/notes:")
for line in fs.ls("/docs/notes"):
    print(line)

print("\n== 读回验证 ==")
data = fs.read("/docs/report.txt")
print(f"  report.txt = {data!r}")
print(f"  长度 {len(data)}B = 70B -> 占 {(len(data) + BLOCK - 1) // BLOCK} 块（含尾部填充）")
print(f"  todo.txt  = {fs.read('/docs/notes/todo.txt')!r}")

print("\n== 覆盖写（先释放再分配）==")
used_before = fs.used_blocks()
fs.write("/docs/report.txt", "short")
print(f"  覆盖为 5B: 释放旧 5 块 -> 新占 1 块，占用 {used_before} -> {fs.used_blocks()}")

print("\n== 删除与空间回收 ==")
fs.delete("/docs/notes/todo.txt")
print(f"  删除 todo.txt -> 占用块 = {fs.used_blocks()}")
print(f"  /docs/notes 内容: {fs.ls('/docs/notes')}")

print("\n== 磁盘满的错误处理 ==")
tiny = MiniFS(4)
tiny.create("/big")
try:
    tiny.write("/big", "X" * 80)          # 需要 5 块 > 4 块
except OSError as exc:
    print(f"  写 80B 到 4 块盘: {type(exc).__name__}: {exc}")

print("\n== 一致性自检（fsck 思想）==")
refs = sum(len(nd["blocks"]) for nd in fs.inodes.values())
claimed = fs.used_blocks()
print(f"  inode 引用块数 = {refs}, 位图标记块数 = {claimed}, 一致: {refs == claimed}")
print("  真实 fsck 还检查：位图与块实际内容、间接块指针、目录项 -> inode 的可达性")

print("\n== 小结 ==")
for line in (
    "  文件系统 = 位图(找块) + inode(元数据) + 目录树(名字) 三层结构",
    "  路径解析自根逐级下钻，任何一级类型不符都要报错",
    "  删除文件的本质是把位图清零 —— 数据块内容不擦，这就是「恢复删除」的原理",
    "  下一课：把 CPU、内存、中断串成一个 tick 驱动的内核循环",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现一级间接块：inode 增加 indirect 指针，把单文件上限从 4 直块扩展到
#    4 + 16 块，验证大文件读写。
# 2. 实现硬链接：同一 inode 可被多个目录项引用，删除最后一个链接才释放块。
# 3. 实现 fsck：遍历目录树收集引用块集合，与位图比对，报告泄漏块/丢失 inode。
# 4. 思考：为什么「先写数据块、再写 inode、最后写位图」的顺序能在崩溃时把
#    损坏限制在「泄漏空间」而不是「错误数据」？
