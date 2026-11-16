# ===== 第669课：有限状态机与工作流-层次状态与历史状态 =====
# 知识点：
#   - 层次状态（HSM）：状态可嵌套，子状态继承父状态的公共转移
#   - 避免「每个子状态都重复写一遍 PAUSE / CANCEL」的组合爆炸
#   - 事件先给最内层子状态处理，未匹配则冒泡到父状态
#   - 历史状态：离开父状态后回来，恢复到上次所在的子状态（浅历史/深历史）
#   - 用路径表示状态：("订单","支付中","等待回调")，父 = 路径前缀
#   - 进入父状态时若有历史记录则直接进入历史子状态
# 依赖：无（标准库）
from dataclasses import dataclass, field


@dataclass
class HSM:
    path: tuple
    history: dict = field(default_factory=dict)   # 父路径 -> 上次的完整子路径
    log: list = field(default_factory=list)

    @property
    def parent(self):
        return self.path[:-1]

    def in_state(self, prefix):
        return self.path[:len(prefix)] == tuple(prefix)


# 转移表：key 是「状态前缀 + 事件」，target 是新的完整路径
TRANSITIONS = {
    # 子状态自己的转移
    (("订单", "支付中", "等待回调"), "回调成功"): ("订单", "支付中", "已确认"),
    (("订单", "支付中", "已确认"), "发货"): ("订单", "配送中", "已出库"),
    (("订单", "配送中", "已出库"), "签收"): ("订单", "完成"),
    # 父状态公共转移（任意子状态都可触发）
    (("订单", "支付中"), "暂停"): ("订单", "已暂停"),
    (("订单", "配送中"), "暂停"): ("订单", "已暂停"),
    (("订单",), "取消"): ("订单", "已取消"),
    (("订单", "已暂停"), "恢复"): "__HISTORY__",
}


def resolve(hsm, event):
    """从最内层前缀向上冒泡，找到第一个匹配的转移。"""
    for depth in range(len(hsm.path), 0, -1):
        key = (hsm.path[:depth], event)
        if key in TRANSITIONS:
            return key[0], TRANSITIONS[key]
    return None, None


def send(hsm, event):
    matched_prefix, target = resolve(hsm, event)
    if target is None:
        hsm.log.append(f"{'/'.join(hsm.path)} --{event}--> 未处理（冒泡到根仍无匹配）")
        return False
    old = hsm.path
    # 记录离开「订单」这个复合状态前的历史
    if len(old) >= 2 and old[0] == "订单":
        hsm.history[("订单",)] = old
    if target == "__HISTORY__":
        new = hsm.history.get(("订单",), ("订单", "支付中", "等待回调"))
    else:
        new = tuple(target)
    hsm.path = new
    hsm.log.append(f"{'/'.join(old)} --{event}--> {'/'.join(new)}  [匹配前缀={'|'.join(matched_prefix)}]")
    return True


h = HSM(("订单", "支付中", "等待回调"))
print("== 正常流程 + 事件冒泡 ==")
for ev in ("回调成功", "发货", "签收"):
    send(h, ev)
    print("  当前:", "/".join(h.path))

print("\n== 父状态公共转移（子状态不必重复定义）==")
h2 = HSM(("订单", "配送中", "已出库"))
print("  起点:", "/".join(h2.path))
send(h2, "暂停")
print("  '暂停' 由父状态 (订单,配送中) 处理 ->", "/".join(h2.path))
h3 = HSM(("订单", "支付中", "已确认"))
send(h3, "取消")
print("  '取消' 由根前缀 (订单,) 处理 ->", "/".join(h3.path))
print("  冒泡顺序：完整路径 -> 逐级截短 -> 根前缀")

print("\n== 历史状态：暂停后恢复到原处 ==")
h4 = HSM(("订单", "支付中", "已确认"))
print("  起点:", "/".join(h4.path))
send(h4, "暂停")
print("  暂停后:", "/".join(h4.path))
print("  记录的历史:", "/".join(h4.history[("订单",)]))
send(h4, "恢复")
print("  恢复后:", "/".join(h4.path), "（回到暂停前的子状态，而不是初始态）")

print("\n== 从不同子状态暂停，恢复位置不同 ==")
for start in (("订单", "支付中", "等待回调"), ("订单", "配送中", "已出库")):
    x = HSM(start)
    send(x, "暂停"); send(x, "恢复")
    print(f"  {'/'.join(start):<24} -> 恢复到 {'/'.join(x.path)}")

print("\n== 完整轨迹 ==")
for line in h4.log:
    print("  -", line)

print("\n== 组合爆炸对比 ==")
children = ["等待回调", "已确认", "已出库", "运输中", "派送中"]
print(f"  若 {len(children)} 个子状态都要写 PAUSE/CANCEL：需 {len(children)*2} 条转移")
print("  用层次状态：父状态各写 1 条，共 2~3 条，且新增子状态零改动")

print("\n== 浅历史 vs 深历史 ==")
for line in (
    "  浅历史 shallow: 只记直接子状态，更深层的嵌套回到默认",
    "  深历史 deep   : 递归记录整条路径，完全回到离开时的叶子",
    "  本例 history 存的是完整路径，属于深历史",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  用元组路径表示嵌套，前缀匹配天然实现冒泡",
    "  历史要持久化，进程重启后也能恢复",
    "  公共转移放父级，特殊转移放子级，优先级由「内到外」保证",
    "  UML Statechart / SCXML 是层次状态机的标准化表达",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现浅历史：恢复时只回到父状态的直接子级。
# 2. 增加 3 层嵌套（订单/售后/退款中），验证事件冒泡跨两级。
# 3. 给进入/离开复合状态加 entry/exit 动作，并处理历史恢复时的触发顺序。
# 4. 思考：为什么「内到外」的冒泡顺序能让子状态覆盖父状态的默认行为？
