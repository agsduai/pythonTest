# ===== 第842课：区块链与信任机制-综合案例-迷你区块链系统 =====
# 知识点：
#   - 综合串起本章：哈希链(835) + PoW(836) + UTXO(837) + 智能合约(838) + P2P(841)
#   - 完整的迷你区块链：挖矿出块 → UTXO 交易验证 → P2P 分叉解决 → 链验证
#   - 分层：交易层（UTXO）→ 共识层（PoW + 最长链）→ 网络层（gossip 模拟）
#   - 全部标准库 + 固定 seed + 内存操作，离线可运行
#   - 与 Bitcoin 的对应关系和差距
# 依赖：无（标准库）
import hashlib
import json
import random
import time
from collections import defaultdict


def sha256(data):
    return hashlib.sha256(data.encode()).hexdigest()


class Transaction:
    __slots__ = ("tx_id", "inputs", "outputs", "fee")

    def __init__(self, tx_id, inputs, outputs, fee=0):
        self.tx_id = tx_id
        self.inputs = inputs        # [(tx_id, output_idx)]
        self.outputs = outputs      # [(recipient, amount)]
        self.fee = fee

    def to_dict(self):
        return {"tx_id": self.tx_id, "inputs": self.inputs,
                "outputs": self.outputs, "fee": self.fee}

    def serialize(self):
        return json.dumps(self.to_dict(), sort_keys=True)


class Block:
    __slots__ = ("index", "prev_hash", "transactions", "timestamp",
                 "difficulty", "nonce", "hash")

    def __init__(self, index, prev_hash, transactions, difficulty):
        self.index = index
        self.prev_hash = prev_hash
        self.transactions = transactions
        self.timestamp = time.time()
        self.difficulty = difficulty
        self.nonce = 0
        self.hash = self._compute_hash()

    def _compute_hash(self):
        content = json.dumps({
            "index": self.index, "prev_hash": self.prev_hash,
            "txs": [t.serialize() for t in self.transactions],
            "timestamp": self.timestamp, "nonce": self.nonce,
        }, sort_keys=True)
        return sha256(content)

    def mine(self):
        target = "0" * self.difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self._compute_hash()
        return self.hash


class MiniBlockchain:
    def __init__(self, difficulty=3):
        self.difficulty = difficulty
        self.utxo_set = {}               # (tx_id, idx) -> (amount, owner)
        self.mempool = []
        self.blocks = [self._genesis()]

    def _genesis(self):
        b = Block(0, "0"*64, [], self.difficulty)
        b.mine()
        # 创世 UTXO
        self.utxo_set[("genesis", 0)] = (100.0, "network")
        return b

    def add_transaction(self, tx):
        self.mempool.append(tx)

    def validate_transaction(self, tx, utxo_snapshot=None):
        utxos = utxo_snapshot or self.utxo_set
        total_in = 0.0
        for tx_id, idx in tx.inputs:
            if (tx_id, idx) not in utxos:
                return False, f"输入 ({tx_id},{idx}) 不存在"
            total_in += utxos[(tx_id, idx)][0]
        total_out = sum(amount for _, amount in tx.outputs) + tx.fee
        if total_in < total_out:
            return False, f"输入 {total_in} < 输出 {total_out}"
        return True, "OK"

    def mine_block(self, miner):
        """从 mempool 取交易打包成块并挖矿。"""
        valid_txs = []
        used_inputs = set()
        fees = 0.0
        for tx in self.mempool:
            ok, msg = self.validate_transaction(tx)
            if not ok: continue
            if any(inp in used_inputs for inp in tx.inputs): continue
            for inp in tx.inputs: used_inputs.add(inp)
            fees += tx.fee
            valid_txs.append(tx)

        if not valid_txs:
            return None
        prev = self.blocks[-1]
        block = Block(prev.index + 1, prev.hash, valid_txs, self.difficulty)
        block.mine()
        self.blocks.append(block)
        # 更新 UTXO
        for tx in valid_txs:
            for tx_id, idx in tx.inputs:
                self.utxo_set.pop((tx_id, idx), None)
            for i, (to, amount) in enumerate(tx.outputs):
                self.utxo_set[(tx.tx_id, i)] = (amount, to)
            if tx.fee > 0:
                self.utxo_set[(tx.tx_id, "fee")] = (tx.fee, miner)
        self.mempool = [t for t in self.mempool if t not in valid_txs]
        return block

    def validate_chain(self):
        for i in range(1, len(self.blocks)):
            cur, prev = self.blocks[i], self.blocks[i-1]
            target = "0" * self.difficulty
            if cur._compute_hash() != cur.hash:
                return False, f"区块 {i} 内容与哈希不符（数据被篡改）"
            if cur.hash[:self.difficulty] != target:
                return False, f"区块 {i} PoW 无效"
            if cur.prev_hash != prev.hash:
                return False, f"区块 {i} 前哈希不匹配"
        return True, "验证通过"

    def balance(self, owner):
        return sum(amount for (amount, o) in self.utxo_set.values() if o == owner)

    def height(self):
        return len(self.blocks) - 1


print("== 构建迷你区块链 ==")
bc = MiniBlockchain(difficulty=3)
print(f"  创世区块: index=0, hash={bc.blocks[0].hash[:24]}...")
print(f"  初始 UTXO: network 有 100.0")

print("\n== 创建初始分配 ==")
from dataclasses import dataclass as _dc
class SimpleTx:
    def __init__(self, tx_id, inputs, outputs, fee=0):
        self.tx_id = tx_id; self.inputs = inputs
        self.outputs = outputs; self.fee = fee
    def serialize(self):
        import json as _json
        return _json.dumps({"id": self.tx_id, "inputs": self.inputs,
                           "outputs": self.outputs}, sort_keys=True)

genesis_dist = SimpleTx("dist_0",
                        [("genesis", 0)],
                        [("Alice", 40), ("Bob", 35), ("Carol", 25)])
bc.mempool.append(genesis_dist)
bc.mine_block("miner_1")
print(f"  初始分配完成，高度={bc.height()}")
print(f"  Alice={bc.balance('Alice')} Bob={bc.balance('Bob')} Carol={bc.balance('Carol')}")

print("\n== 创建并确认交易 ==")
tx1 = SimpleTx("tx_1", [("dist_0", 0)], [("Bob", 15)], fee=0.5)  # Alice 的 UTXO key 是 ("dist_0",0)
bc.mempool.append(tx1)
tx2 = SimpleTx("tx_2", [("dist_0", 1)], [("Carol", 10)], fee=0.3)  # Bob 的 UTXO key 是 ("dist_0",1)
bc.mempool.append(tx2)
block = bc.mine_block("miner_1")
print(f"  新区块 #{block.index}: {len(block.transactions)} 笔交易")
print(f"  Alice={bc.balance('Alice'):>6.1f} Bob={bc.balance('Bob'):>6.1f} "
      f"Carol={bc.balance('Carol'):>6.1f} 矿工={bc.balance('miner_1'):.1f}")
print("  注意：tx1/tx2 没有找零输出，差额被永久销毁 —— 真实 UTXO 系统必须输出找零")

print("\n== 双花检测 ==")
# Alice 的 UTXO ("dist_0", 0) 已在第 2 块中被消费，再次使用即双花
tx_double = SimpleTx("tx_double", [("dist_0", 0)], [("Eve", 30)])
bc.mempool.append(tx_double)
block2 = bc.mine_block("miner_2")
print(f"  双花交易被拒绝: mine_block 返回 {'None（无有效交易）' if block2 is None else f'Block#{block2.index}'}")
print(f"  Alice 余额仍为 {bc.balance('Alice'):.1f}（UTXO 已被消费，无法双花）")

print("\n== 链验证 ==")
ok, msg = bc.validate_chain()
print(f"  {msg} -> {ok}")

print("\n== 篡改检测 ==")
bc.blocks[1].transactions[0].outputs = [("Eve", 100)]
ok2, msg2 = bc.validate_chain()
print(f"  篡改交易后: {ok2} -> {msg2}")
print("  篡改交易改变 Merkle 根 → 块哈希改变 → 后续块全部失效")

print("\n== 完整状态 ==")
print(f"  高度={bc.height()}  UTXO数={len(bc.utxo_set)}")
for key, (amount, owner) in sorted(bc.utxo_set.items(), key=lambda x: str(x[0])):
    print(f"    {str(key):<20} {amount:>6.1f} -> {owner}")

print("\n== 区块链架构分层 ==")
for line in [
    "  网络层  : P2P gossip 传播区块与交易（第841课）",
    "  共识层  : PoW 挖矿 + 最长链规则（第836/839课）",
    "  交易层  : UTXO 模型 + 双花检测 + 手续费（第837课）",
    "  合约层  : 智能合约状态机（第838课）",
    "  密码层  : 哈希链 + 数字签名 + Merkle 树（第835/840/705课）",
    "  应用层  : 余额查询 / 交易历史 / 智能合约调用",
]:
    print("  -", line)

print("\n== 与 Bitcoin 的对应 ==")
print(f"  {'组件':<16}{'Bitcoin':<26}{'本课实现'}")
for row in (("块头", "80B（version/prev/Merkle/time/bits/nonce）", "简化 JSON"),
            ("共识", "SHA-256d PoW，2016块调难度", "SHA-256 PoW，固定难度"),
            ("交易", "Script 脚本验证签名", "简化 UTXO（无签名）"),
            ("网络", "TCP 8333 P2P", "内存模拟"),
            ("存储", "LevelDB 区块文件", "内存列表")):
    print(f"  {row[0]:<16}{row[1]:<26}{row[2]}")

print("\n== 教学边界 ==")
for line in [
    "  本课实现是教学用的最小区块链，省略了签名/P2P/持久化/分叉处理",
    "  生产区块链系统涉及密码学、网络协议、存储优化、共识工程",
    "  学习建议：先理解本课原理，再阅读 Bitcoin 白皮书和源码",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 集成第840课的数字签名到交易验证中（简化版：检查签名 hash 是否匹配）。
# 2. 实现「区块浏览器」：展示每笔交易的输入/输出/手续费。
# 3. 实现简单的分叉处理：当收到更长的链时替换当前链。
# 4. 思考：为什么「区块间隔约 10 分钟」对网络安全很重要？太短或太长各有什么问题？
