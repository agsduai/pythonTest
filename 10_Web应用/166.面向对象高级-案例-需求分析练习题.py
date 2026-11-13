# ===== 第166课：面向对象高级-案例-需求分析 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 需求分析：先明确“做什么”，再考虑“怎么做”
#   - 图书会员管理系统的角色：书籍、会员、借阅记录、管理员
#   - 核心功能：登录、查看书籍、借书、还书、查看借阅情况
#   - 业务规则：库存不能为负，会员有借阅上限，登录后才能借还
#   - 根据需求划分类：Book、Member、NormalMember、VipMember、Library


from dataclasses import dataclass


@dataclass
class Requirement:
    """一条需求：所属模块、功能描述、优先级。"""

    module: str
    feature: str
    priority: str


requirements = [
    Requirement("书籍", "记录编号、书名、作者、总库存", "高"),
    Requirement("书籍", "借出后库存减一，归还后库存加一", "高"),
    Requirement("会员", "记录会员号、姓名、密码、借阅列表", "高"),
    Requirement("会员", "普通会员最多借 3 本，VIP 最多借 6 本", "中"),
    Requirement("登录", "会员号加密码登录，错误时给出提示", "高"),
    Requirement("借阅", "登录后才能借书、还书，并检查库存与上限", "高"),
]

print("图书会员管理系统 - 需求清单")
for index, req in enumerate(requirements, start=1):
    print(f"{index}. [{req.module}] {req.feature}（优先级：{req.priority}）")

high_priority = [req for req in requirements if req.priority == "高"]
print(f"\n高优先级需求共 {len(high_priority)} 项，应优先实现")

class_plan = {
    "Book": "书籍信息：编号、书名、作者、库存",
    "Member": "会员抽象基类：姓名、密码、借阅上限",
    "NormalMember": "普通会员，最多借 3 本",
    "VipMember": "VIP 会员，最多借 6 本",
    "Library": "管理书籍与会员，提供登录、借书、还书",
}
print("\n类设计规划：")
for class_name, duty in class_plan.items():
    print(f"  {class_name}: {duty}")

# ===== 练习题 =====
# 1. 为系统补充“查询借阅记录”需求，写入 requirements 列表并重新输出。
# 2. 写一个函数，按模块筛选需求并返回该模块的需求数量。
# 3. 思考：为什么先做需求分析，再开始写类？举一个需求遗漏的例子。
