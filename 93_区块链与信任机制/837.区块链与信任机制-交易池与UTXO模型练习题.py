# ===== 第837课：区块链与信任机制-交易池与UTXO模型 =====
# 知识点：
#   - UTXO（Unspent Transaction Output）：每个交易消耗旧的 UTXO 并产生新的 UTXO
#   - 与账户模型的区别：UTXO 更像现金（每张钞票独立），账户模型像银行账户
#   - 双花检测：同一 UTXO 被两次消费 = 双花，第二笔应被拒绝
#   - 交易验证：输入总额 ≥ 输出总额（差额 = 手续费），签名验证
#   - 交易池 mempool：等待被打包进区块的交易
#   - 本课实现 UTXO 模型的创建/消费/双花检测
# 依赖：无（标准库）
import hashlib
import time


def tx_hash(tx_id):
    return hashlib.sha256(tx_id.encode()).hexdigest()[:16]


class UTXO:
    __slots__ = ("tx_id", "output_index", "amount", "owner")

    def __init__(self, tx_id, output_index, amount, owner):
        self.tx_id = tx_id
        self.output_index = output_index
        self.amount = amount
        self.owner = owner

    @property
    def key(self):
        return f"{self.tx_id}:{self.output_index}"

    def __repr__(self):
        return f"UTXO({self.key}, {self.amount}, {self.owner})"


class UTXOLedger:
    def __init__(self):
        self.utxos = {}               # key -> UTXO
        self.mempool = []             # 待打包的交易
        self.confirmed = []           # 已确认的交易

    def create_coinbase(self, to, amount):
        tx_id = tx_hash(f"coinbase_{to}_{amount}_{time.time()}")
        utxo = UTXO(tx_id, 0, amount, to)
        self.utxos[utxo.key] = utxo
        return utxo

    def create_transaction(self, sender, inputs, outputs, fee=0):
        """inputs = [UTXO], outputs = [(recipient, amount)]"""
        # 验证输入存在且属于 sender
        total_in = 0
        for utxo in inputs:
            key = utxo.key if isinstance(utxo, UTXO) else utxo
            if key not in self.utxos:
                return None, f"输入 {key} 不存在"
            u = self.utxos[key]
            if u.owner != sender:
                return None, f"输入 {key} 不属于 {sender}"
            total_in += u.amount

        total_out = sum(amount for _, amount in outputs) + fee
        if total_in < total_out:
            return None, f"输入总额 {total_in} < 输出总额 {total_out}"

        # 构造交易
        tx_id = tx_hash(f"{sender}_{inputs[0].key}_{total_out}_{time.time()}")
        tx = {
            "id": tx_id, "sender": sender,
            "inputs": [u.key if isinstance(u, UTXO) else u for u in inputs],
            "outputs": [(to, amt, f"{tx_id}:{i}") for i, (to, amt) in enumerate(outputs)],
            "fee": fee,
        }
        self.mempool.append(tx)
        return tx, "OK"

    def confirm_transaction(self, tx):
        """把交易确认：删除输入 UTXO，创建输出 UTXO。"""
        for input_key in tx["inputs"]:
            if input_key in self.utxos:
                del self.utxos[input_key]
        for i, (to, amount, out_key) in enumerate(tx["outputs"]):
            utxo = UTXO(tx["id"], i, amount, to)
            self.utxos[utxo.key] = utxo
        self.mempool.remove(tx)
        self.confirmed.append(tx)

    def double_spend_check(self, tx):
        """检查交易的输入是否已被其他 mempool 交易消费。"""
        used_inputs = set()
        for t in self.mempool:
            used_inputs.update(t["inputs"])
        conflicts = set(tx["inputs"]) & used_inputs
        return len(conflicts) > 0, conflicts

    def balance(self, owner):
        return sum(u.amount for u in self.utxos.values() if u.owner == owner)

    def utxos_for(self, owner):
        return [u for u in self.utxos.values() if u.owner == owner]


print("== 初始状态：挖矿生成初始 UTXO ==")
ledger = UTXOLedger()
ledger.create_coinbase("Alice", 50)
ledger.create_coinbase("Bob", 30)
print(f"  Alice: {ledger.utxos_for('Alice')}")
print(f"  Bob: {ledger.utxos_for('Bob')}")

print("\n== 正常交易：Alice 转给 Bob 20 ==")
alice_utxos = ledger.utxos_for("Alice")
tx, msg = ledger.create_transaction("Alice", alice_utxos, [("Bob", 20)], fee=1)
print(f"  {msg}")
if tx:
    print(f"  交易: id={tx['id']} inputs={tx['inputs']} outputs={tx['outputs']} fee={tx['fee']}")
    # 双花检测
    ds, conflicts = ledger.double_spend_check(tx)
    print(f"  双花检测: {ds} 冲突={conflicts}")
    ledger.confirm_transaction(tx)
    print(f"  确认后 Alice 余额={ledger.balance('Alice')} Bob 余额={ledger.balance('Bob')}")

print("\n== 双花攻击：同一 UTXO 花两次 ==")
bob_utxos = ledger.utxos_for("Bob")
tx1, _ = ledger.create_transaction("Bob", bob_utxos, [("Carol", 10)])
if tx1:
    ledger.confirm_transaction(tx1)
# 用已被消费的输入再创建一笔交易
old_input = [u for u in ledger.utxos_for("Bob")]  # 只剩未花掉的
# 手动构造使用旧输入的交易
tx2, msg2 = ledger.create_transaction("Bob", ledger.utxos_for("Bob"), [("Carol", 5)])
print(f"  正常交易: {msg2}")

# 尝试双花：用已被消费的 Alice 的 UTXO
spent_key = list(ledger.utxos.keys())   # 当前的所有 UTXO
from dataclasses import dataclass
stale_utxo = UTXO("old_tx", 0, 50, "Alice")   # 伪造一个已被消费的 UTXO
tx3, msg3 = ledger.create_transaction("Alice", [stale_utxo], [("Dave", 40)])
print(f"  双花交易: {msg3}")
print("  UTXO 模型天然防双花：消费即删除 UTXO，不存在就报错")

print("\n== 找零（change） ==")
alice_balance = ledger.balance("Alice")
alice_available = ledger.utxos_for("Alice")
if alice_available:
    tx4, msg4 = ledger.create_transaction("Alice", alice_available,
                                          [("Bob", 10)], fee=1)
    if tx4:
        # 找零输出给 Alice
        total_in = sum(ledger.utxos[u].amount for u in tx4["inputs"]
                       if u in ledger.utxos)
        change = total_in - 10 - 1
        if change > 0:
            tx4["outputs"].append(("Alice", change, f"change_{tx4['id']}"))
            print(f"  找零给 Alice: {change}")
        ledger.confirm_transaction(tx4)
print(f"  最终 Alice 余额={ledger.balance('Alice')}")

print("\n== mempool 与确认 ==")
print(f"  mempool 交易数={len(ledger.mempool)}")
print(f"  已确认交易数={len(ledger.confirmed)}")

print("\n== UTXO vs 账户模型 ==")
print(f"  {'维度':<14}{'UTXO 模型':<24}{'账户模型'}")
for row in (("存储", "未花费输出集合", "账户余额表"),
            ("并行", "不同 UTXO 可并行", "同一账户需锁"),
            ("隐私", "每次用新地址", "地址固定"),
            ("双花", "删除 UTXO 即防", "需要序号/nonce"),
            ("典型", "Bitcoin", "Ethereum")):
    print(f"  {row[0]:<14}{row[1]:<24}{row[2]}")

print("\n== 工程要点 ==")
for line in [
    "  UTXO 的 key = (tx_id, output_index)，全局唯一",
    "  交易的输入输出必须平衡（总额守恒），差额 = 矿工费",
    "  签名验证省略了：真实 Bitcoin 用 ECDSA 验证所有权",
    "  mempool 按手续费排序，矿工优先打包高费交易",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「找零输出」：输入大于输出时，差额作为找零返回给发送者。
# 2. 实现「手续费市场」：mempool 按手续费/大小排序，矿工打包高费交易。
# 3. 实现「多签名 UTXO」：需要 2 个签名才能消费（简化为检查签名列表）。
# 4. 思考：为什么 Bitcoin 选择 UTXO 而不是账户模型？
