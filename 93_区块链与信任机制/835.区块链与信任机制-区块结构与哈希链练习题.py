# ===== 第835课：区块链与信任机制-区块结构与哈希链 =====
# 知识点：
#   - 区块 = 块头（前块哈希、时间戳、Merkle 根、nonce）+ 交易列表
#   - 哈希链：每个区块包含前一个区块的哈希，篡改任何区块都会导致后续全部失效
#   - 创世区块：链的第一个区块，无前驱
#   - 与第705课 Merkle 树的区别：705 讲证明结构，这里讲区块链的区块头与链式结构
#   - 本课用标准库 hashlib 构建一个简单的哈希链，验证不可篡改性
# 依赖：无（标准库）
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Optional


def sha256(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


@dataclass
class Block:
    index: int
    timestamp: float
    data: str
    previous_hash: str
    nonce: int = 0

    def hash(self):
        content = json.dumps({
            "index": self.index, "timestamp": self.timestamp,
            "data": self.data, "previous_hash": self.previous_hash,
            "nonce": self.nonce,
        }, sort_keys=True)
        return sha256(content)


class Blockchain:
    def __init__(self):
        self.chain = [self._genesis()]

    def _genesis(self):
        return Block(0, 0.0, "Genesis Block", "0"*64)

    def add_block(self, data):
        prev = self.chain[-1]
        block = Block(len(self.chain), time.time(), data, prev.hash())
        self.chain.append(block)
        return block

    def is_valid(self):
        """验证整条链：哈希链接 + 索引连续。"""
        for i in range(1, len(self.chain)):
            cur, prev = self.chain[i], self.chain[i-1]
            if cur.hash() != sha256(json.dumps({
                "index": cur.index, "timestamp": cur.timestamp,
                "data": cur.data, "previous_hash": prev.hash(),
                "nonce": cur.nonce,
            }, sort_keys=True)):
                return False, f"区块 {i} 哈希不匹配"
            if cur.previous_hash != prev.hash():
                return False, f"区块 {i} 的 previous_hash 不匹配"
            if cur.index != prev.index + 1:
                return False, f"区块 {i} 索引不连续"
        return True, "整条链验证通过"

    def tamper(self, index, new_data):
        """篡改某个区块的数据。"""
        self.chain[index].data = new_data


print("== 构建区块链 ==")
bc = Blockchain()
blocks_data = ["Alice 转给 Bob 5 BTC", "Bob 转给 Carol 3 BTC", "Carol 转给 Dave 2 BTC"]
for data in blocks_data:
    b = bc.add_block(data)
    print(f"  Block #{b.index}: data={data!r} hash={b.hash()[:24]}...")

print("\n== 区块链验证（未篡改） ==")
ok, msg = bc.is_valid()
print(f"  {msg} -> {ok}")

print("\n== 篡改区块 1 的数据 ==")
bc.tamper(1, "Alice 转给 Eve 999 BTC")
ok, msg = bc.is_valid()
print(f"  篡改后验证: {ok} -> {msg}")
print("  区块 1 的哈希改变 → 区块 2 的 previous_hash 不匹配 → 链断裂")
print("  要让篡改生效，必须重算区块 1 及之后所有区块的哈希 → 计算昂贵")

print("\n== 恢复篡改（重新计算所有后续区块） ==")
# 篡改者需要重算整条链
for i in range(1, len(bc.chain)):
    bc.chain[i].previous_hash = bc.chain[i-1].hash()
    # 注意：没有 PoW 时重算成本为零 → 需要 PoW 增加成本（第836课）
ok, msg = bc.is_valid()
print(f"  重算后验证: {ok} -> {msg}")
print("  无 PoW 时篡改者可以重算整条链 → 需要 PoW 让重算成本远高于诚实节点")

print("\n== 区块结构详解 ==")
b = bc.chain[0]
print(f"  index: {b.index}")
print(f"  timestamp: {b.timestamp}")
print(f"  data: {b.data!r}")
print(f"  previous_hash: {b.previous_hash!r}")
print(f"  nonce: {b.nonce}")
print(f"  hash: {b.hash()[:32]}...")

print("\n== 哈希链 vs Merkle 树 ==")
for line in (
    "  哈希链: 块 N 包含块 N-1 的哈希，验证整条链需 O(n)",
    "  Merkle 树: 叶→根的二叉树，验证单条数据只需 O(log n) 的路径",
    "  区块链同时用两者：块头存 Merkle 根（验证交易），块间用哈希链（保证顺序）",
    "  Bitcoin 用 Merkle 树让轻节点（SPV）不用下载全部交易就能验证",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  真实区块链的块头还有 version/bits/Merkle root 等（Bitcoin 80 字节头）",
    "  时间戳必须单调递增（或至少不倒退），否则链无效",
    "  生产区块链用 protobuf/自定义序列化，不用 json.dumps",
    "  本课是「哈希链」的最小实现，不含 PoW/P2P/共识",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给 Block 加 Merkle root 字段，用第705课的 Merkle 树存储交易列表。
# 2. 实现「链分叉」：两个节点从同一高度各自添加区块。
# 3. 实现「区块高度」的检查：确保没有跳过任何高度。
# 4. 思考：为什么哈希链需要「前一个哈希」而不是「前一个区块的完整内容」？
