# ===== 第907课：差分隐私与联邦学习-隐私攻击与k-匿名 =====
# 知识点：
#   - 发布数据集前必须回答：谁能从里面认出谁？
#   - 链接攻击：把发布表与外部知识（如选民登记表）按准标识符连接
#   - 准标识符（QI）：看似无害、组合起来却唯一的属性（邮编+生日+性别）
#   - k-匿名：每个 QI 组合至少 k 条记录 —— 但有同质攻击与背景知识攻击
#   - l-多样性：每个 QI 组内敏感属性至少 l 种不同取值
# 依赖：无（标准库）
from collections import Counter


def make_raw_data():
    """模拟医院发布表：邮编 + 年龄 + 性别 + 疾病。"""
    rows = [
        ("210000", 34, "男", "流感"),
        ("210000", 34, "男", "心肌梗死"),
        ("210000", 27, "女", "流感"),
        ("210000", 27, "女", "流感"),
        ("100000", 55, "男", "流感"),
        ("100000", 55, "男", "流感"),
        ("100000", 55, "男", "癌症"),
        ("310000", 41, "女", "流感"),
        ("310000", 41, "女", "流感"),
        ("310000", 23, "男", "艾滋病"),
    ]
    return rows


def qi_groups(rows, qi_cols):
    groups = {}
    for r in rows:
        key = tuple(r[qi_cols.index(c)] for c in qi_cols)
        groups.setdefault(key, []).append(r)
    return groups


def k_anonymity_level(rows, qi_cols):
    groups = qi_groups(rows, qi_cols)
    return min(len(v) for v in groups.values())


def generalization_map():
    """泛化层级：邮编 -> 前缀；年龄 -> 区间。"""
    return {
        "邮编3": lambda r: (r[0][:3], r[1] // 10 * 10, r[2]),
        "邮编2": lambda r: (r[0][:2], r[1] // 10 * 10, r[2]),
        "邮编2+年龄5岁": lambda r: (r[0][:2], r[1] // 5 * 5, r[2]),
        "邮编1+年龄10岁": lambda r: (r[0][:1], r[1] // 10 * 10, r[2]),
    }


print("== 原始发布表 ==")
rows = make_raw_data()
print(f"  {'邮编':<8}{'年龄':>4}{'性别':>4}{'疾病'}")
for r in rows:
    print(f"  {r[0]:<8}{r[1]:>4}{r[2]:>4}  {r[3]}")
qi = ["邮编", "年龄", "性别"]
print(f"\n  k-匿名水平（QI=邮编+年龄+性别）= {k_anonymity_level(rows, qi)}")
groups = qi_groups(rows, qi)
for key, members in groups.items():
    if len(members) == 1:
        print(f"  唯一记录组 {key}: {members[0][3]} —— 直接暴露！")

print("\n== 链接攻击演示 ==")
auxiliary = {("210000", 34, "男")}         # 攻击者知道某人 34 岁男住 210000
matches = [r for r in rows if (r[0], r[1], r[2]) in auxiliary]
print(f"  攻击者外部知识: {auxiliary}")
print(f"  匹配记录 = {matches} -> 疾病必然是 {matches[0][3]}（k=1 直接命中）")

print("\n== 逐步泛化到 k-匿名 ==")
print(f"  {'方案':<16}{'k-匿名水平':>10}  说明")
for label, fn in generalization_map().items():
    generalized = [fn(r) + (r[3],) for r in rows]
    k = k_anonymity_level(generalized, ["邮编", "年龄", "性别"])
    note = "达标" if k >= 2 else "仍不足"
    print(f"  {label:<16}{k:>10}  {note}")
best = "邮编2+年龄5岁"
generalized = [generalization_map()[best](r) + (r[3],) for r in rows]
print(f"\n  选择方案 [{best}]:")
print(f"  {'QI组':<22}{'疾病列表':<28}{'组大小':>6}")
for key, members in sorted(qi_groups(generalized, ["邮编", "年龄", "性别"]).items()):
    diseases = "/".join(m[3] for m in members)
    print(f"  {str(key):<22}{diseases:<28}{len(members):>6}")

print("\n== 同质攻击：k-匿名的漏洞 ==")
for key, members in qi_groups(generalized, ["邮编", "年龄", "性别"]).items():
    diseases = set(m[3] for m in members)
    if len(diseases) == 1 and len(members) > 1:
        print(f"  组 {key}: k={len(members)} 但疾病全是『{members[0][3]}』")
        print("    -> 攻击者不需要唯一性也能确定疾病（同质攻击）")

print("\n== l-多样性检查 ==")
for label, fn in (("邮编2+年龄5岁", generalization_map()[best]),):
    generalized = [fn(r) + (r[3],) for r in rows]
    groups = qi_groups(generalized, ["邮编", "年龄", "性别"])
    l_level = min(len(set(m[3] for m in members)) for members in groups.values())
    print(f"  {label}: l-多样性 = {l_level}")
print("  l=2 才算能抵御同质攻击；不足时需要继续泛化或加入虚假行（慎用）")

print("\n== k-匿名的根本局限 ==")
for line in (
    "  k-匿名只保证『你混在 k 个人里』，不保证『你的敏感值不唯一』",
    "  攻击者的背景知识可以进一步缩小范围（背景知识攻击）",
    "  泛化过度 → 数据可用性崩塌；这是一个无法两全的硬权衡",
    "  差分隐私（908 课）给出数学化的强定义：不看你是谁，看你影响什么",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  隐私风险不在单列，而在组合：QI 组合的唯一性才是要害",
    "  k-匿名/l-多样性是语法层面的防护，实现简单、可解释",
    "  同质攻击说明语法防护有天花板 -> 需要语义级保证（DP）",
    "  记住这条链：链接攻击 -> k-匿名 -> l-多样性 -> 差分隐私",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 l-多样性加强版（熵 l-多样性）：组内敏感分布的熵 ≥ log(l)。
# 2. 实现 Mondrian 多维划分算法：贪心切分 QI 空间直到每组满足 k-匿名。
# 3. 用「最长公共前缀」自动推导最小泛化层级（目标 k=2）。
# 4. 思考：为什么「删除姓名」完全不够？列举三个能重新识别的准标识符。
