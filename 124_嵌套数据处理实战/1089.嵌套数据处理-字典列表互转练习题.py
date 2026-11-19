# ===== 第1089课：嵌套数据处理-字典列表互转 =====
# 知识点：
#   - 列表 -> 字典：以某字段为键建索引（id_map = {u["id"]: u for u in users}）
#   - 字典 -> 列表：items() 转成 [(键, 值), ...] 或 [{'key': k, 'value': v}]
#   - "索引字典"价值：按 id 查找从 O(n) 遍历变 O(1) 直接取
#   - 两列表合字典：dict(zip(keys, values))（116 章学过，这里用于数据重组）

# 案例一：列表转索引字典
# 场景：用户列表按 id 建索引，方便查找
users = [
    {"id": 101, "name": "小张", "vip": True},
    {"id": 102, "name": "小李", "vip": False},
    {"id": 103, "name": "小王", "vip": True},
]
user_map = {u["id"]: u for u in users}
print(f"索引字典：{user_map}")
print(f"按 id 查 102：{user_map[102]['name']}（不用再遍历）")

# 案例二：索引字典查存在的键
def find_user(uid):
    return user_map.get(uid, "查无此人")

print(f"103：{find_user(103)['name']}，999：{find_user(999)}")

# 案例三：字典转列表
# 场景：把 {商品: 价格} 转成接口要的 [{"name": ..., "price": ...}]
price_map = {"苹果": 5.5, "牛奶": 8.0, "面包": 12.0}
goods_list = [{"name": k, "price": v} for k, v in price_map.items()]
print(f"转列表：{goods_list}")

# 案例四：两级结构重组
# 场景：{班级: {姓名: 分数}} 转成扁平记录列表便于统计
class_scores = {"一班": {"小张": 90, "小李": 85}, "二班": {"小王": 92}}
flat = [
    {"cls": cls, "name": name, "score": score}
    for cls, scores in class_scores.items()
    for name, score in scores.items()
]
print(f"扁平化：{flat}")

# 案例五：列表转"多值索引" —— 一个键对应多条记录
# 场景：按班级分组所有学生
from collections import defaultdict

cls_map = defaultdict(list)
for u in users:
    cls_map["vip" if u["vip"] else "普通"].append(u["name"])
print(f"按会员分组：{dict(cls_map)}")

# ===== 练习题 =====
# 1. 把商品列表 [{"code":"A1","name":"苹果"},...] 转成 {code: name} 的映射字典，打印按 code 查名称。
# 2. 把 {"语文": 88, "数学": 92} 转成 [{"subject": ..., "score": ...}] 列表，并按分数降序排列。
# 3. 双向互转练习：先做 1 的映射字典，再把映射字典转回 [{"code": ..., "name": ...}]，验证与原始列表内容一致（顺序可能不同，把两个列表都按 code 排序后再用 == 比较）。
