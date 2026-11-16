# ===== 第391课：设计模式进阶-责任链模式 =====
# 知识点：
#   - 责任链：请求沿链传递，谁能处理谁处理，处理不了就交给下一环
#   - 每环只关心自己的规则，新增审批级别不改已有代码（开闭原则）
#   - 链的末端兜底：没人处理时给出明确的“拒绝/转人工”
#   - 与第258课工厂、第259课策略的区别：链是“逐级尝试”，不是“选择算法”
from abc import ABC, abstractmethod


class ExpenseRequest:

    def __init__(self, applicant: str, amount: float, reason: str):
        self.applicant, self.amount, self.reason = applicant, amount, reason


class Approver(ABC):

    def __init__(self, name: str):
        self.name = name
        self.next: "Approver | None" = None

    def set_next(self, approver: "Approver") -> "Approver":
        self.next = approver
        return approver                     # 支持 a.set_next(b).set_next(c) 链式组装

    @abstractmethod
    def can_approve(self, req: ExpenseRequest) -> bool: ...

    def handle(self, req: ExpenseRequest) -> str:
        if self.can_approve(req):
            return f"{self.name} 批准了 {req.applicant} 的 {req.amount:.0f} 元（{req.reason}）"
        if self.next:
            print(f"  {self.name}：超出权限，转交 {self.next.name}")
            return self.next.handle(req)
        return f"无人可批：{req.amount:.0f} 元超出所有审批人权限"


class TeamLead(Approver):
    LIMIT = 1000

    def can_approve(self, req):
        return req.amount <= self.LIMIT


class Manager(Approver):
    LIMIT = 5000

    def can_approve(self, req):
        return req.amount <= self.LIMIT


class Director(Approver):
    LIMIT = 20000

    def can_approve(self, req):
        return req.amount <= self.LIMIT


# ---- 组装链：组长 → 经理 → 总监 ----
lead = TeamLead("组长小王")
manager = Manager("经理李姐")
director = Director("总监张总")
lead.set_next(manager).set_next(director)

requests = [
    ExpenseRequest("小明", 300, "团建"),
    ExpenseRequest("小红", 3000, "设备采购"),
    ExpenseRequest("小刚", 15000, "差旅"),
    ExpenseRequest("小丽", 50000, "场地租赁"),
]

print("== 审批流程 ==")
for req in requests:
    print(f"\n申请：{req.applicant} / {req.amount:.0f} 元 / {req.reason}")
    print("结果：", lead.handle(req))

# ---- 动态插队：临时加一个“财务复核”环节 ----
print("\n== 插入财务复核后 ==")


class FinanceCheck(Approver):
    """金额 >= 10000 必须先过财务；它只复核，不负责最终批准。"""

    def can_approve(self, req):
        return False                  # 本环节从不做最终批准

    def handle(self, req):
        if req.amount >= 10000:
            print(f"  {self.name}：{req.amount:.0f} 元已复核")
        return self.next.handle(req) if self.next else "复核后无人审批"


# 插在“经理”和“总监”之间
finance = FinanceCheck("财务部")
manager.set_next(finance).set_next(director)
print(lead.handle(ExpenseRequest("小美", 12000, "培训")))

# ===== 练习题 =====
# 1. 增加“副总裁”一级（限额 100000），接在总监之后。
# 2. 给链加“拒绝短路”：金额为负时直接拒绝，不再往下传。
# 3. 思考：责任链太长会有什么问题？如何避免“谁都不处理”？
