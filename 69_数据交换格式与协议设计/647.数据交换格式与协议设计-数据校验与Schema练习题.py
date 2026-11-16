# ===== 第647课：数据交换格式与协议设计-数据校验与Schema =====
# 知识点：
#   - Schema 是「协议的可执行文档」：字段名、类型、必填、取值范围、嵌套结构
#   - 校验要「先结构后业务」：类型/必填 -> 格式/范围 -> 跨字段约束
#   - 收集全部错误而非遇错即停，一次反馈所有问题，对接方体验更好
#   - 手写轻量校验器：spec 用 dict 描述，validate 返回 (ok, errors, cleaned)
#   - 清洗（coerce）与校验分离：先尝试安全转换，再做约束判断
#   - JSON Schema / pydantic 是工业方案，本课用标准库演示核心思想
# 依赖：无（标准库）
from datetime import datetime

MISSING = object()


def validate(data, spec, path=""):
    """按 spec 校验 data，返回 (errors, cleaned)。"""
    errors, cleaned = [], {}
    for field, rule in spec.items():
        if field.startswith("__"):        # __cross__ 等元信息不是字段规则
            continue
        key = f"{path}.{field}" if path else field
        raw = data.get(field, MISSING)
        if raw is MISSING:
            if rule.get("required"):
                errors.append(f"{key}: 缺少必填字段")
            elif "default" in rule:
                cleaned[field] = rule["default"]
            continue
        expected = rule["type"]
        value = raw
        # 安全转换（只允许窄范围，避免 "123abc" 被吞掉）
        if rule.get("coerce") and expected is int and isinstance(raw, str):
            if raw.strip().lstrip("+-").isdigit():
                value = int(raw)
        if expected is int and isinstance(value, bool):
            errors.append(f"{key}: bool 不算 int")
            continue
        if not isinstance(value, expected):
            errors.append(f"{key}: 类型应为 {expected.__name__}，实际 {type(value).__name__}")
            continue
        if "min" in rule and value < rule["min"]:
            errors.append(f"{key}: {value} 小于最小值 {rule['min']}")
        if "max" in rule and value > rule["max"]:
            errors.append(f"{key}: {value} 超过最大值 {rule['max']}")
        if "choices" in rule and value not in rule["choices"]:
            errors.append(f"{key}: {value!r} 不在 {rule['choices']} 中")
        if "pattern" in rule and not rule["pattern"].search(str(value)):
            errors.append(f"{key}: 格式不符合 {rule['pattern'].pattern}")
        if "max_len" in rule and len(value) > rule["max_len"]:
            errors.append(f"{key}: 长度 {len(value)} 超过 {rule['max_len']}")
        cleaned[field] = value

    # 跨字段约束
    for rule_fn, msg in spec.get("__cross__", []):
        try:
            if not rule_fn(cleaned):
                errors.append(f"{path or 'root'}: {msg}")
        except (KeyError, TypeError):
            pass
    return errors, cleaned


import re
USER_SPEC = {
    "id": {"type": int, "required": True, "min": 1},
    "name": {"type": str, "required": True, "min_len": 2, "max_len": 20},
    "email": {"type": str, "required": True,
              "pattern": re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")},
    "age": {"type": int, "required": False, "default": 0, "min": 0, "max": 150,
            "coerce": True},
    "role": {"type": str, "required": True, "choices": ("admin", "user", "guest")},
    "tags": {"type": list, "required": False, "default": []},
    "__cross__": [
        (lambda d: d.get("role") != "admin" or d.get("age", 0) >= 18,
         "管理员必须年满 18 岁"),
    ],
}
# min_len 由通用校验器不认识，这里补一条简单处理：改用 max_len + 自定义
def validate_user(data):
    errors, cleaned = validate(data, USER_SPEC)
    name = cleaned.get("name")
    if isinstance(name, str) and "min_len" in USER_SPEC["name"]:
        if len(name) < USER_SPEC["name"]["min_len"]:
            errors.append(f"name: 长度 {len(name)} 小于 {USER_SPEC['name']['min_len']}")
    return errors, cleaned


print("== 合法数据 ==")
good = {"id": 1, "name": "张三", "email": "a@b.com", "age": "25", "role": "admin", "tags": ["vip"]}
errs, clean = validate_user(good)
print("  错误:", errs or "无")
print("  清洗后:", clean)
print("  age 从字符串安全转成 int:", type(clean["age"]).__name__)

print("\n== 一次收集全部错误 ==")
bad = {"id": 0, "name": "A", "email": "not-an-email", "age": 200,
       "role": "root", "extra": "ignored"}
errs, _ = validate_user(bad)
for e in errs:
    print("  -", e)
print(f"  共 {len(errs)} 条错误（一次性返回，不是遇到第一个就停）")

print("\n== 必填缺失与默认值 ==")
errs, clean = validate_user({"id": 2, "name": "李四", "email": "l@x.cn", "role": "user"})
print("  错误:", errs or "无")
print("  默认值生效:", {k: clean[k] for k in ("age", "tags")})

print("\n== 跨字段约束 ==")
for payload in (
    {"id": 3, "name": "王五", "email": "w@x.cn", "role": "admin", "age": 16},
    {"id": 4, "name": "赵六", "email": "z@x.cn", "role": "admin", "age": 20},
):
    errs, _ = validate_user(payload)
    print(f"  age={payload['age']}: {errs or '通过'}")

print("\n== 类型陷阱：bool 是 int 的子类 ==")
errs, _ = validate_user({"id": True, "name": "测试", "email": "t@x.cn", "role": "user"})
print("  ", errs)

print("\n== 嵌套结构：递归校验 ==")
ORDER_SPEC = {
    "order_id": {"type": str, "required": True},
    "amount": {"type": (int, float), "required": True, "min": 0},
}
# 通用校验器支持 tuple 类型
def validate_order(data):
    errs, cleaned = {}, {}
    for field, rule in ORDER_SPEC.items():
        raw = data.get(field, MISSING)
        if raw is MISSING:
            errs.setdefault("errors", []).append(f"{field}: 缺少必填")
            continue
        if not isinstance(raw, rule["type"]):
            errs.setdefault("errors", []).append(f"{field}: 类型错误")
            continue
        if "min" in rule and raw < rule["min"]:
            errs.setdefault("errors", []).append(f"{field}: {raw} 小于最小值 {rule['min']}")
            continue
        cleaned[field] = raw
    return errs.get("errors", []), cleaned

for o in ({"order_id": "A1", "amount": 99.5}, {"order_id": "A2", "amount": -1}):
    print(f"  {o} -> {validate_order(o)[0] or '通过'}")

print("\n== Schema 即协议文档 ==")
for line in [
    "把 spec 导出成 JSON Schema / OpenAPI，供前端与对接方生成代码",
    "版本升级：新增字段设 required=False + default，老消息照样过",
    "严格模式：未知字段报错；宽松模式：忽略（本例忽略 extra）",
    "永远在信任边界校验：入口一次，内部就按已校验结构处理",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给通用校验器补上 min_len、items（列表元素类型）、nested（嵌套 spec）。
# 2. 实现 strict 模式：出现未声明字段时报错，而不是静默忽略。
# 3. 把 USER_SPEC 导出成一份人类可读的 Markdown 字段表。
# 4. 思考：为什么「收集全部错误」比「遇到第一个错误就抛异常」更适合对外 API？
