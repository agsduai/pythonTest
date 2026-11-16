# ===== 第648课：数据交换格式与协议设计-版本兼容与演进 =====
# 知识点：
#   - 兼容性两个方向：向后兼容（新代码读旧数据）、向前兼容（旧代码读新数据）
#   - 破坏性变更：删字段、改字段类型/含义、改必填、改枚举取值语义
#   - 安全演进：加可选字段、加新枚举值、加新接口版本、用 default 兜底
#   - 迁移链：v1 -> v2 -> v3 逐级 upgrade，禁止跳级；每条迁移可单测
#   - 双写/影子读：过渡期同时写新旧格式，灰度切读，验证一致后再下线旧版
#   - 语义化版本：MAJOR 不兼容、MINOR 兼容新增、PATCH 兼容修复
# 依赖：无（标准库）
from copy import deepcopy

print("== 兼容性的两个方向 ==")
for line in (
    "  向后兼容 backward: 新解析器能读旧消息（加字段时靠 default）",
    "  向前兼容 forward : 旧解析器能读新消息（靠忽略未知字段）",
    "  两者兼顾的关键   : 未知字段不报错 + 缺失字段有默认值",
):
    print(line)


def parse(payload, spec):
    """按 spec 解析：缺字段取 default，未知字段忽略，支持 rename。"""
    out = {}
    for key, rule in spec.items():
        source = rule.get("from", key)
        if source in payload:
            out[key] = payload[source]
        elif "default" in rule:
            out[key] = rule["default"]()
        elif rule.get("required"):
            raise ValueError(f"缺少必填字段 {source}")
    return out


V1_SPEC = {
    "user": {"required": True},
    "amount": {"required": True},
}
V2_SPEC = {
    "user": {"from": "user", "required": True},
    "amount": {"from": "amount", "required": True},
    "currency": {"default": lambda: "CNY"},
    "channel": {"default": lambda: "web"},
}
V3_SPEC = {
    "user_id": {"from": "user", "required": True},
    "amount_cents": {"required": True},
    "currency": {"default": lambda: "CNY"},
    "channel": {"default": lambda: "web"},
    "tags": {"default": list},
}

print("\n== v1 消息被 v2 解析器读取（向后兼容）==")
v1 = {"user": "alice", "amount": 100}
print("  v1:", v1)
print("  v2 解析:", parse(v1, V2_SPEC))

print("\n== v2 消息被 v1 解析器读取（向前兼容）==")
v2 = {"version": 2, "user": "bob", "amount": 200,
      "currency": "USD", "channel": "app", "extra": 1}
print("  v2:", v2)
print("  v1 解析（忽略未知字段）:", parse(v2, V1_SPEC))

print("\n== 破坏性变更示例 ==")
bad_changes = [
    ("amount: number -> string", "改类型", "旧代码算数会崩"),
    ("删除 user 字段", "删字段", "必填校验失败"),
    ("status: 0/1 改成 'ok'/'fail'", "改枚举语义", "判断逻辑全错"),
    ("新增必填字段且无默认值", "改必填", "旧消息全部拒绝"),
]
for change, kind, impact in bad_changes:
    print(f"  {change:<34} [{kind}] -> {impact}")

print("\n== 迁移链：逐级 upgrade，禁止跳级 ==")
def upgrade_v1_to_v2(d):
    d = deepcopy(d)
    d.setdefault("currency", "CNY")
    d.setdefault("channel", "web")
    d["version"] = 2
    return d


def upgrade_v2_to_v3(d):
    d = deepcopy(d)
    d["user_id"] = d.pop("user")
    d["amount_cents"] = int(round(d.pop("amount") * 100))
    d.setdefault("tags", [])
    d["version"] = 3
    return d


MIGRATIONS = {1: upgrade_v1_to_v2, 2: upgrade_v2_to_v3}

def migrate(payload, target=3):
    d = deepcopy(payload)
    v = d.get("version", 1)
    if v > target:
        raise ValueError(f"不能把 v{v} 降级到 v{target}")
    while v < target:
        if v not in MIGRATIONS:
            raise ValueError(f"缺少 v{v}->v{v+1} 的迁移")
        d = MIGRATIONS[v](d)
        v = d["version"]
    return d

print("  v1 -> v3:", migrate(v1))
print("  v2 -> v3:", migrate(v2))
print("  已是 v3 :", migrate({"version": 3, "user_id": "c", "amount_cents": 500}))
try:
    migrate({"version": 3}, target=2)
except ValueError as e:
    print("  拒绝降级:", e)

print("\n== 迁移链单测：逐级幂等与不丢数据 ==")
for start in (1, 2):
    out = migrate(v1 if start == 1 else v2)
    print(f"  起点 v{start}: 终态 version={out['version']} "
          f"user_id={out.get('user_id')} amount_cents={out.get('amount_cents')}")

print("\n== 双写 / 影子读（灰度过渡）==")
def dual_write(record):
    return {"old": parse(record, V1_SPEC), "new": migrate(record)}

shadow = dual_write(v1)
print("  同时写:", shadow)
print("  影子读比对 old.amount*100 == new.amount_cents:",
      shadow["old"]["amount"] * 100 == shadow["new"]["amount_cents"])
print("  比对一致一段时间后，才把读切到新格式并下线旧版")

print("\n== 语义化版本 ==")
for ver, meaning in (("1.2.3 -> 1.2.4", "PATCH：兼容的 bug 修复"),
                     ("1.2.3 -> 1.3.0", "MINOR：兼容的新增字段/接口"),
                     ("1.2.3 -> 2.0.0", "MAJOR：不兼容变更，需迁移")):
    print(f"  {ver:<18} {meaning}")

print("\n== 协议演进清单 ==")
for line in [
    "每条消息带 version，解析器按版本分派",
    "新增字段一律可选 + 默认值；枚举预留 UNKNOWN 兜底",
    "字段只增不删；废弃字段标记 deprecated，保留两个大版本",
    "迁移函数成对写（up/down），并针对真实历史样本做回归测试",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 downgrade_v3_to_v2，并验证 v1->v3->v2 的数据损失范围。
# 2. 给 parse 增加 deprecated 字段告警，统计线上还有多少旧字段在用。
# 3. 设计「枚举 UNKNOWN 兜底」，演示旧代码读到新枚举值时不会崩。
# 4. 思考：为什么「逐级迁移」比「直接 v1 转 v3」更不容易出错？
