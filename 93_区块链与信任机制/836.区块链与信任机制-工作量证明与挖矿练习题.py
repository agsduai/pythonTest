# ===== 第836课：区块链与信任机制-工作量证明与挖矿 =====
# 知识点：
#   - PoW（Proof of Work）：找到一个 nonce 使区块哈希满足难度条件（前 N 位为 0）
#   - 难度 difficulty：目标哈希的前导零位数；难度越高越难找
#   - 挖矿 = 暴力搜索 nonce；每次尝试改变 nonce，哈希完全改变
#   - 难度调整：定期调整使出块时间稳定（Bitcoin 每 2016 块调整一次）
#   - 51% 攻击：控制超过 50% 算力的节点可以重写历史
#   - 本课实现 PoW 挖矿（低难度）并分析难度与时间的关系
# 依赖：无（标准库）
import hashlib
import time
import math


class PoWBlock:
    def __init__(self, index, data, prev_hash, difficulty=4):
        self.index = index
        self.timestamp = time.time()
        self.data = data
        self.previous_hash = prev_hash
        self.difficulty = difficulty
        self.nonce = 0
        self.hash = self._mine()

    def _hash(self):
        content = f"{self.index}{self.timestamp}{self.data}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _mine(self):
        """暴力搜索 nonce 直到哈希满足难度条件。"""
        target = "0" * self.difficulty
        nonce = 0
        while True:
            h = self._hash_with_nonce(nonce)
            if h.startswith(target):
                return nonce
            nonce += 1

    def _hash_with_nonce(self, nonce):
        content = f"{self.index}{self.timestamp}{self.data}{self.previous_hash}{nonce}"
        return hashlib.sha256(content.encode()).hexdigest()

    def __repr__(self):
        return f"Block#{self.index} nonce={self.nonce} hash={self._hash_with_nonce(self.nonce)[:16]}..."


class PoWBlockchain:
    def __init__(self, difficulty=4):
        self.difficulty = difficulty
        self.chain = []
        genesis = self._create_genesis()
        self.chain.append(genesis)

    def _create_genesis(self):
        b = PoWBlock(0, "Genesis", "0"*64, self.difficulty)
        return b

    def add_block(self, data):
        prev = self.chain[-1]
        b = PoWBlock(len(self.chain), data, prev._hash_with_nonce(prev.nonce), self.difficulty)
        self.chain.append(b)
        return b

    def is_valid(self):
        target = "0" * self.difficulty
        for i in range(1, len(self.chain)):
            cur, prev = self.chain[i], self.chain[i-1]
            if cur._hash_with_nonce(cur.nonce)[:self.difficulty] != target:
                return False, f"区块 {i} 的 PoW 无效"
            if cur.previous_hash != prev._hash_with_nonce(prev.nonce):
                return False, f"区块 {i} 的 previous_hash 不匹配"
        return True, "整条 PoW 链验证通过"


print("== PoW 挖矿：难度 vs 时间 ==")
for difficulty in (3, 4, 5):
    bc = PoWBlockchain(difficulty=difficulty)
    t0 = time.perf_counter()
    bc.add_block("test data")
    dt = time.perf_counter() - t0
    b = bc.chain[-1]
    print(f"  难度={difficulty} ({'0'*difficulty}前缀): nonce={b.nonce} 耗时={dt*1000:.1f}ms")
print("  难度每 +1，期望耗时 ×16（16 = 16进制字符空间 / 前导零概率）")
print("  这里用小难度保持课程运行时间可控；Bitcoin 当前难度对应约 10 分钟/块")

print("\n== 构建 PoW 区块链 ==")
bc4 = PoWBlockchain(difficulty=4)
bc4.add_block("Transaction 1")
bc4.add_block("Transaction 2")
print(f"  链长度={len(bc4.chain)}")
for b in bc4.chain:
    print(f"  Block#{b.index}: nonce={b.nonce} hash={b._hash_with_nonce(b.nonce)[:20]}...")

print("\n== PoW 链验证 ==")
ok, msg = bc4.is_valid()
print(f"  {msg} -> {ok}")

print("\n== 篡改 PoW 链的代价 ==")
# 篡改区块 1 并重算 PoW
tampered = PoWBlockchain(difficulty=4)
tampered.chain = [b for b in bc4.chain]
tampered.chain[1].data = "被篡改的数据"
# 需要重算 nonce
import hashlib as _h
for i in range(1, len(tampered.chain)):
    blk = tampered.chain[i]
    blk.previous_hash = tampered.chain[i-1]._hash_with_nonce(tampered.chain[i-1].nonce)
    t0 = time.perf_counter()
    blk.nonce = 0
    target = "0" * blk.difficulty
    while True:
        h = blk._hash_with_nonce(blk.nonce)
        if h.startswith(target): break
        blk.nonce += 1
    dt = (time.perf_counter()-t0)*1000
    print(f"  重算 Block#{blk.index} nonce={blk.nonce} 耗时={dt:.1f}ms")
ok, msg = tampered.is_valid()
print(f"  重算后验证: {ok} -> {msg}")
print("  篡改者成功重算了链 → 但这只在「没有诚实节点竞争」时可行")
print("  真实区块链：诚实节点持续追加区块，篡改者需要超过 50% 的算力才能追上")

print("\n== 51% 攻击模拟 ==")
print("  攻击者算力占比 = 30%:")
print("    诚实节点每分钟挖 7 块，攻击者挖 3 块")
print("    攻击者私有链永远追不上公共链 → 攻击失败")
print("  攻击者算力占比 = 60%:")
print("    攻击者私有链增长更快 → 最终追上公共链 → 可以重写历史")
print("  但：重写历史会损害系统信任 → 代币价值归零 → 攻击者自损")

print("\n== 工程要点 ==")
for line in [
    "  Bitcoin 用 SHA-256 双重哈希（hash(hash(block_header))）",
    "  难度用「目标值」而非前导零位数，支持更精细的调整",
    " nonce 的搜索空间 2^32 有限，用 extra_nonce 扩展",
    "  PoW 消耗大量能源 → PoS（权益证明）替代方案正在普及",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「难度动态调整」：根据最近 N 块的实际出块时间调整 difficulty。
# 2. 模拟 51% 攻击：诚实节点和攻击者并行挖矿，统计私有链何时追上。
# 3. 实现「双花攻击」：同一笔钱在两条分叉上花两次，分析哪条链胜出。
# 4. 思考：为什么 PoW 需要「nonce」而不能直接用时间戳作为可变字段？
