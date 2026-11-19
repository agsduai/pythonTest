# ===== 第1011课：综合小项目实战-综合案例-个人信息管理器 =====
# 知识点：
#   - 综合：字典存储 + 文件持久化 + 输入验证 + 异常处理 + 菜单交互
#   - 一个完整的 CRUD 应用：增查改删 + 统计 + 搜索 + 持久化
#   - 函数分层：数据层（load/save）、逻辑层（增删改查）、交互层（菜单）
#   - 出错不崩溃：所有用户输入都有容错
# 依赖：无（标准库）
import json
import os

DATA_FILE = "profiles.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("  ⚠ 数据文件损坏，已重置")
        return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------- 功能函数 ----------
def add_person(data, name, age, city):
    if not name.strip():
        return False, "姓名不能为空"
    if name in data:
        return False, f"{name} 已存在"
    try:
        age = int(age)
    except ValueError:
        return False, "年龄必须是数字"
    if not 1 <= age <= 150:
        return False, f"年龄 {age} 超出范围 (1-150)"
    data[name] = {"age": age, "city": city.strip() or "未知"}
    save_data(data)
    return True, f"已添加 {name} ({age}岁, {data[name]['city']})"


def search_person(data, keyword):
    """模糊搜索：姓名包含关键词就算匹配。"""
    results = []
    for name, info in data.items():
        if keyword.lower() in name.lower():
            results.append((name, info))
    return results


def update_person(data, name, field, value):
    if name not in data:
        return False, f"{name} 不存在"
    if field == "age":
        try:
            value = int(value)
        except ValueError:
            return False, "年龄必须是数字"
        if not 1 <= value <= 150:
            return False, f"年龄 {value} 超出范围"
    data[name][field] = value
    save_data(data)
    return True, f"已更新 {name} 的 {field} 为 {value}"


def delete_person(data, name):
    if name not in data:
        return False, f"{name} 不存在"
    removed = data.pop(name)
    save_data(data)
    return True, f"已删除 {name} ({removed['age']}岁, {removed['city']})"


def show_all(data):
    if not data:
        print("    （暂无数据）")
        return
    print(f"    {'姓名':<8}{'年龄':>6}{'城市':<12}")
    print(f"    {'-' * 28}")
    for name, info in sorted(data.items()):
        print(f"    {name:<8}{info['age']:>6}{info['city']:<12}")


# ---------- 运行示例 ----------
print("== 个人信息管理器 ==")
data = load_data()

print("\n== 添加 ==")
for args in [("张三", "25", "北京"), ("李四", "30", "上海"),
             ("王五", "28", "广州"), ("赵六", "abc", "深圳")]:
    name = args[0]
    ok, msg = add_person(data, *args)
    print(f"  添加 {name}: {msg}")

print("\n== 当前数据 ==")
show_all(data)

print("\n== 搜索 ==")
results = search_person(data, "张")
for name, info in results:
    print(f"  找到 {name}: {info['age']}岁, {info['city']}")
if not results:
    print("  未找到")

print("\n== 修改 ==")
ok, msg = update_person(data, "张三", "age", "26")
print(f"  {msg}")
ok, msg = update_person(data, "李四", "city", "杭州")
print(f"  {msg}")

print("\n== 删除 ==")
ok, msg = delete_person(data, "赵六")
print(f"  {msg}")
ok, msg = delete_person(data, "不存在的")
print(f"  {msg}")

print("\n== 最终数据 ==")
show_all(data)

print("\n== 统计 ==")
if data:
    ages = [info["age"] for info in data.values()]
    print(f"  人数: {len(data)}")
    print(f"  平均年龄: {sum(ages) / len(ages):.1f}")
    print(f"  最大: {max(ages)}, 最小: {min(ages)}")

# 清理演示文件
os.remove(DATA_FILE)
print(f"\n  已清理 {DATA_FILE}")

# ===== 练习题 =====
# 1. 给个人信息增加「电话」字段并更新 add 和 update 函数。
# 2. 实现「按城市分组统计」：每个城市有多少人。
# 3. 实现「数据导出」：把所有人信息保存为 CSV 文件。
# 4. 思考：这个项目的数据层/逻辑层/交互层各包含哪些函数？如果要加
#    「数据加密存储」，需要改哪一层？
