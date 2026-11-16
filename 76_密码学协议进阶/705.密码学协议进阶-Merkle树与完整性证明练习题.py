# ===== 第705课：密码学协议进阶-Merkle树与完整性证明 =====
# 知识点：
#   - Merkle 树：叶子是数据块哈希，父节点 = H(left || right)，逐层聚合成单个根
#   - 根哈希只需 32 字节就能「承诺」整批数据；改任一叶，根必变
#   - Merkle Proof（包含证明）：给出从叶到根路径上兄弟节点哈希，验证者 O(log n) 复算根
#   - 奇数个节点时复制最后一个（或按 Bitcoin 的做法）补齐
#   - 应用：区块链 SPV、Git 对象、证书透明日志、文件分块校验、增量同步
#   - 要防「第二原像攻击」：区分叶哈希与内部哈希（加不同前缀）
# 依赖：无（标准库）
import hashlib
import hmac
from dataclasses import dataclass

LEAF_PREFIX, NODE_PREFIX = b"\x00", b"\x01"

def h(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

def leaf_hash(item: str) -> bytes:
    return h(LEAF_PREFIX + item.encode())

def node_hash(left: bytes, right: bytes) -> bytes:
    return h(NODE_PREFIX + left + right)


class MerkleTree:
    def __init__(self, items):
        self.leaves = [leaf_hash(x) for x in items]
        if not self.leaves:
            raise ValueError("至少需要一个数据块")
        self.levels = [self.leaves]
        cur = self.leaves
        while len(cur) > 1:
            if len(cur) % 2:
                cur = cur + [cur[-1]]          # 奇数个：复制最后一个
            cur = [node_hash(cur[i], cur[i + 1]) for i in range(0, len(cur), 2)]
            self.levels.append(cur)
        self.root = self.levels[-1][0]

    def proof(self, index):
        """返回 [(兄弟哈希, 是左兄弟?)] 自底向上。"""
        out, idx = [], index
        for level in self.levels[:-1]:
            if len(level) % 2:
                level = level + [level[-1]]
            sibling = idx ^ 1
            out.append((level[sibling], idx % 2 == 1))  # True 表示兄弟在左边
            idx //= 2
        return out

    @staticmethod
    def verify(item, proof, root):
        cur = leaf_hash(item)
        for sib, sib_is_left in proof:
            cur = node_hash(sib, cur) if sib_is_left else node_hash(cur, sib)
        return hmac.compare_digest(cur, root)


items = ["tx1", "tx2", "tx3", "tx4", "tx5"]
t = MerkleTree(items)
print("== Merkle 树 ==")
print(f"  叶子 {len(t.leaves)} 个，共 {len(t.levels)} 层")
for i, level in enumerate(t.levels):
    print(f"  层 {i}: {len(level)} 个节点  " +
          " ".join(x.hex()[:8] for x in level[:4]))
print(f"  root = {t.root.hex()}")

print("\n== 包含证明（O(log n)）==")
for idx in (0, 2, 4):
    proof = t.proof(idx)
    ok = MerkleTree.verify(items[idx], proof, t.root)
    print(f"  叶 {idx} {items[idx]!r}: 路径长度={len(proof)} 验证={ok}")
    print("    路径:", [(s.hex()[:8], "左" if left else "右") for s, left in proof])

print("\n== 篡改检测 ==")
proof = t.proof(2)
print("  用正确数据:", MerkleTree.verify("tx3", proof, t.root))
print("  改成 txX  :", MerkleTree.verify("txX", proof, t.root))
bad_root = h(b"tampered")
print("  伪造根    :", MerkleTree.verify("tx3", proof, bad_root))

print("\n== 根随数据变化（雪崩效应）==")
for delta in ("tx1", "tx2", "tx6"):
    other = MerkleTree([delta if i == 0 else x for i, x in enumerate(items)])
    print(f"  改第 0 块为 {delta!r}: root={other.root.hex()[:16]}... 相同={other.root == t.root}")

print("\n== 增量更新成本 ==")
n = 1024
print(f"  {n} 个叶子：")
print(f"    全量重算: {n} 次叶哈希 + {n-1} 次内部哈希")
print(f"    更新 1 叶: 只重算 {n.bit_length()-1} 个祖先节点（log2({n})）")
print("    这是 Merkle 树适合大文件 / 增量同步的核心原因")

print("\n== 前缀区分防第二原像 ==")
a, b = b"a", b"b"
internal = node_hash(leaf_hash("a"), leaf_hash("b"))
fake_leaf = leaf_hash("internal-looks-like-this")
print(f"  叶哈希前缀={LEAF_PREFIX.hex()} 内部哈希前缀={NODE_PREFIX.hex()}")
print(f"  某个内部节点被当成叶子解读时: {hmac.compare_digest(internal, fake_leaf)}")
print("  不同前缀让「内部节点」与「叶节点」落在不同哈希域，攻击无法混用")

print("\n== 应用对照 ==")
for line in (
    "  Bitcoin SPV : 轻节点只存区块头里的 Merkle root，用 proof 验证交易",
    "  Git         : 树对象本质是 Merkle 结构，commit 哈希承诺整个目录",
    "  CT 日志     : 证书透明用 Merkle 树 + 审计证明防 CA 偷偷签发",
    "  分块下载    : 每块带 proof，边下边验，不必等整个文件",
):
    print(" ", line)

print("\n== 工程注意 ==")
for line in [
    "  奇数节点补齐策略要写进协议，否则双方算出的根不同",
    "  叶/内部哈希加不同前缀（或不同哈希函数）是必须的",
    "  proof 要带叶子索引与树大小，防止把叶当内部节点",
    "  生产用 audited 实现；稀疏 Merkle 树 / Verkle 树是进阶方向",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现多叶证明（一次证明若干个叶子都在树里），复用公共路径省空间。
# 2. 实现「不存在证明」：在排序 Merkle 树里证明某个键未被包含。
# 3. 对比 1000 叶时「逐个校验」与「Merkle proof」的传输字节数。
# 4. 思考：为什么叶哈希与内部哈希必须加不同前缀？
