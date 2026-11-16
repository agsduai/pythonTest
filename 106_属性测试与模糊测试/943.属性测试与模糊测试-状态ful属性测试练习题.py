# ===== 第943课：属性测试与模糊测试-状态ful属性测试 =====
# 知识点：
#   - 单次调用测不到「交互序列」的 bug：状态残留、次序依赖、缓存失效
#   - 状态ful 测试：随机命令序列 + 简单模型对照 —— 每步验证系统与模型一致
#   - 与 100 章模型检测的关系：同构！只是「状态」由模型类表示、转移由命令实现
#   - 命令带前置条件（guard）：只在合法状态下执行
#   - 失败时缩小命令序列：删步/化简参数 —— 941 课思想用在序列上
# 依赖：无（标准库）
import random


# ---------- 被测系统：一个有 bug 的迷你 KV 存储 ----------
class BuggyKV:
    """故意藏 bug：删除后重写同名键会读到旧值（状态残留）。"""

    def __init__(self):
        self.store = {}
        self.deleted = set()

    def put(self, key, value):
        if key in self.deleted:
            self.store[key] = ("旧值-" + str(value),)      # bug 在这里
        else:
            self.store[key] = (value,)

    def get(self, key):
        return self.store.get(key, (None,))[0]

    def delete(self, key):
        if key in self.store:
            self.store.pop(key)
        self.deleted.add(key)


class CorrectKV:
    """模型（神谕）：行为与规格一致。"""

    def __init__(self):
        self.store = {}

    def put(self, key, value):
        self.store[key] = (value,)

    def get(self, key):
        return self.store.get(key, (None,))[0]

    def delete(self, key):
        self.store.pop(key, None)


# ---------- 命令定义 ----------
class PutCommand:
    @staticmethod
    def guard(model, key=None, value=None):
        return True

    @staticmethod
    def run(system, key, value):
        system.put(key, value)

    @staticmethod
    def run_model(model, key, value):
        model.put(key, value)


class GetCommand:
    @staticmethod
    def guard(model, key=None, **_):
        return key in model.store

    @staticmethod
    def verify(model, system, key):
        expected = model.get(key)
        actual = system.get(key)
        return actual == expected, (key, expected, actual)


class DeleteCommand:
    @staticmethod
    def guard(model, key=None, **_):
        return key in model.store

    @staticmethod
    def run(system, key, value=None):
        system.delete(key)

    @staticmethod
    def run_model(model, key, value=None):
        model.delete(key)


COMMANDS = [("put", PutCommand), ("get", GetCommand), ("delete", DeleteCommand)]
KEYS = ["k1", "k2", "k3"]
VALUES = [1, 2, 3]


def random_command(rng):
    name, cls = rng.choice(COMMANDS)
    key = rng.choice(KEYS)
    value = rng.choice(VALUES)
    return {"name": name, "cls": cls, "key": key, "value": value}


def execute_sequence(rng, max_steps=15):
    """执行随机命令序列；返回 (失败序列, 失败详情) 或 None。"""
    system = BuggyKV()
    model = CorrectKV()
    sequence = []
    for _ in range(max_steps):
        cmd = random_command(rng)
        kwargs = {"key": cmd["key"], "value": cmd["value"]}
        if not cmd["cls"].guard(model, **kwargs):
            continue
        sequence.append(cmd)
        if cmd["name"] == "put":
            cmd["cls"].run(system, **kwargs)
            cmd["cls"].run_model(model, **kwargs)
        elif cmd["name"] == "delete":
            cmd["cls"].run(system, **kwargs)
            cmd["cls"].run_model(model, **kwargs)
        else:
            ok, detail = cmd["cls"].verify(model, system, cmd["key"])
            if not ok:
                return sequence, detail
    return None, None


def shrink_sequence(sequence):
    """缩小命令序列：逐条删除后重放，仍失败则保留删除。"""

    def still_fails(seq):
        system = BuggyKV()
        model = CorrectKV()
        for cmd in seq:
            kwargs = {"key": cmd["key"], "value": cmd["value"]}
            if not cmd["cls"].guard(model, **kwargs):
                continue
            if cmd["name"] == "put":
                cmd["cls"].run(system, **kwargs)
                cmd["cls"].run_model(model, **kwargs)
            elif cmd["name"] == "delete":
                cmd["cls"].run(system, **kwargs)
                cmd["cls"].run_model(model, **kwargs)
            else:
                ok, _ = cmd["cls"].verify(model, system, cmd["key"])
                if not ok:
                    return True
        return False

    current = list(sequence)
    improved = True
    while improved:
        improved = False
        for i in range(len(current)):
            candidate = current[:i] + current[i + 1:]
            if candidate and still_fails(candidate):
                current = candidate
                improved = True
                break
    return current


rng = random.Random(143)

print("== 被测系统与模型 ==")
print("  BuggyKV（藏 bug）：删除后重写同键会返回『旧值-…』")
print("  CorrectKV（模型）：put 后 get 必须读到刚写入的值")
print("  命令集：put / get(前置：键存在) / delete(前置：键存在)")

print("\n== 随机命令序列搜索 ==")
found = None
for trial in range(300):
    sequence, detail = execute_sequence(rng)
    if sequence is not None:
        found = (sequence, detail, trial)
        break
if found:
    sequence, detail, trial = found
    print(f"  第 {trial + 1} 轮发现失败！命令序列长度 {len(sequence)}")
    for cmd in sequence:
        args = f"{cmd['key']}" + (f", {cmd['value']}" if cmd["name"] == "put" else "")
        print(f"    {cmd['name']}({args})")
    print(f"  失败详情: get({detail[0]!r}) 期望 {detail[1]!r}, 实际 {detail[2]!r}")
else:
    print("  300 轮未发现失败（不应发生，bug 很容易踩中）")

print("\n== 缩小命令序列 ==")
minimal = shrink_sequence(sequence)
print(f"  {len(sequence)} 步 -> {len(minimal)} 步的最小序列:")
for cmd in minimal:
    args = f"{cmd['key']}" + (f", {cmd['value']}" if cmd["name"] == "put" else "")
    print(f"    {cmd['name']}({args})")
print("  最小序列直指 bug 本质：put k v → delete k → put k v2 → get k 读到旧值")
print("  —— 状态残留类 bug 的标准指纹")

print("\n== 与模型检测（100 章）的对照 ==")
print(f"  {'维度':<14}{'模型检测':<22}{'状态ful属性测试'}")
for row in (("搜索方式", "穷举/符号遍历全部状态", "随机采样命令序列"),
            ("完备性", "完备（可证明）", "概率性（找不到≠没有）"),
            ("状态表示", "显式状态集合", "可执行的模型类"),
            ("适用场景", "协议/规则逻辑", "任何有接口的系统")):
    print(f"  {row[0]:<14}{row[1]:<22}{row[2]}")
print("  思想同源：模型对照 + 转移遍历；后者把『验证』工程化为『测试』")

print("\n== 前置条件的作用 ==")
print("  get/delete 只在『键存在』时执行 —— 否则模型的 get 返回 None")
print("  会让验证永远通过（无意义的比较）")
print("  guard 让随机命令聚焦在有意义的转移上 —— 覆盖效率的关键")

print("\n== 小结 ==")
for line in (
    "  状态ful 测试 = 命令序列 + 双执行（系统/模型）+ 逐步一致断言",
    "  guard 前置条件保证命令合法；缩小器把长序列压成最小复现",
    "  状态残留/次序依赖/缓存失效这类 bug 的天敌",
    "  944 课：另一种找 bug 的方式 —— 不加断言的模糊测试",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 给 BuggyKV 再加一个 bug（如 delete 后 size 不减），验证状态ful 测试
#    能否同时抓到两个 bug。
# 2. 实现缩小器第二阶段：把命令参数替换为「首选值」（key 恒为 k1）。
# 3. 把命令集扩展为「批量 put」与「遍历」，观察覆盖变化。
# 4. 思考：模型类的复杂度应占被测系统的几成？太像被测系统会失去什么，
#    太简单又会失去什么？
