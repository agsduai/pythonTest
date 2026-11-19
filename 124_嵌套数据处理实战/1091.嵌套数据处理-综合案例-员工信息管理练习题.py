# ===== 第1091课：嵌套数据处理-综合案例-员工信息管理 =====
# 知识点：
#   - 综合运用：过滤 / 排序 / 分组 / 汇总 / 更新 / 索引
#   - 数据管理程序套路：查列表 -> 查单个 -> 增改删 -> 统计报表
#   - 每个"功能"写成小函数，主流程像菜单一样串联
#   - 修改数据时同步维护索引字典，避免两边不一致

# 案例一：员工数据与索引
employees = [
    {"id": "E01", "name": "小张", "dept": "技术", "salary": 15000},
    {"id": "E02", "name": "小李", "dept": "销售", "salary": 9000},
    {"id": "E03", "name": "小王", "dept": "技术", "salary": 12000},
    {"id": "E04", "name": "小赵", "dept": "人事", "salary": 8000},
]
index = {e["id"]: e for e in employees}

# 案例二：查询功能
def list_all():
    print("--- 员工名单 ---")
    for e in sorted(employees, key=lambda x: x["id"]):
        print(f"{e['id']} {e['name']} {e['dept']} {e['salary']}")

def find(eid):
    return index.get(eid)

print(f"查找 E02：{find('E02')['name']}，查找 E99：{find('E99')}")

# 案例三：增改删
def add_employee(eid, name, dept, salary):
    if eid in index:
        print(f"工号 {eid} 已存在")
        return False
    emp = {"id": eid, "name": name, "dept": dept, "salary": salary}
    employees.append(emp)
    index[eid] = emp
    print(f"新增：{name}")
    return True

def update_salary(eid, new_salary):
    emp = find(eid)
    if emp is None:
        print(f"工号 {eid} 不存在")
        return False
    emp["salary"] = new_salary
    print(f"{emp['name']} 薪资更新为 {new_salary}")
    return True

def remove_employee(eid):
    emp = find(eid)
    if emp is None:
        return False
    employees.remove(emp)
    del index[eid]
    print(f"删除：{emp['name']}")
    return True

add_employee("E05", "小周", "技术", 11000)
update_salary("E02", 10500)
remove_employee("E04")
list_all()

# 案例四：统计报表
from collections import defaultdict

def report():
    dept_stats = defaultdict(lambda: [0, 0.0])
    for e in employees:
        dept_stats[e["dept"]][0] += 1
        dept_stats[e["dept"]][1] += e["salary"]
    print("--- 部门报表 ---")
    for dept, (cnt, total) in sorted(dept_stats.items(), key=lambda kv: -kv[1][1]):
        print(f"{dept}：{cnt} 人，平均 {total / cnt:.0f} 元")

report()

# 案例五：筛选高薪员工
high_salary = sorted(
    (e for e in employees if e["salary"] >= 11000),
    key=lambda e: -e["salary"],
)
print("--- 高薪榜（>=11000）---")
for e in high_salary:
    print(f"{e['name']}（{e['dept']}）：{e['salary']}")

# ===== 练习题 =====
# 1. 写函数 rename(eid, new_name)：更新姓名并校验工号存在，用 E03 改名"王小明"测试。
# 2. 写函数 top_paid(n)：返回工资前 n 名的 (姓名, 薪资) 列表，测试 n=3。
# 3. 综合挑战：为 add_employee 增加工资范围校验（0~50000，超出打印原因返回 False），并测试三种输入。
