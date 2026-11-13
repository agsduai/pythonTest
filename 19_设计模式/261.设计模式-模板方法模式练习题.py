# ===== 第261课：设计模式-模板方法模式 =====
# 知识点：
#   - 模板方法：父类定死“流程骨架”，子类只填具体步骤
#   - 好处：流程统一不跑偏，步骤可替换
#   - 场景：数据导出（读取→处理→写出）、测试流程、爬虫流程
#   - 与策略的区别：策略换“整个算法”，模板方法换“流程中的某几步”

from abc import ABC, abstractmethod


class ReportExporter(ABC):
    """模板：export 定死三步流程，子类只实现两个钩子。"""

    def export(self, data) -> str:
        rows = self.format(data)      # 步骤1：格式化（子类实现）
        return self.write(rows)       # 步骤2：输出（子类实现）

    @abstractmethod
    def format(self, data): ...

    @abstractmethod
    def write(self, rows): ...

    def header(self):                 # 可选钩子：有默认行为，子类可覆盖
        return "== 报表 =="


class CsvReport(ReportExporter):

    def format(self, data):
        return "\n".join(f"{k},{v}" for k, v in data.items())

    def write(self, rows):
        return f"{self.header()}\n{rows}"


class JsonReport(ReportExporter):

    def __init__(self, indent=2):
        self.indent = indent

    def format(self, data):
        import json
        return json.dumps(data, ensure_ascii=False, indent=self.indent)

    def write(self, rows):
        return rows                   # JSON 不需要额外头部


class ConsoleReport(ReportExporter):
    """演示钩子覆盖：换成自己的头部。"""

    def format(self, data):
        return "\n".join(f"· {k}: {v}" for k, v in data.items())

    def write(self, rows):
        return f"【控制台预览】\n{rows}"

    def header(self):
        return "★ 仪表盘 ★"


data = {"课程": "Python进阶", "课时": 36, "价格": 199}
for exporter in (CsvReport(), JsonReport(), ConsoleReport()):
    print(exporter.export(data))
    print("-" * 30)

# ===== 练习题 =====
# 1. 给 ReportExporter 增加第三步 log()：在 export 流程末尾统一打日志。
# 2. 实现Excel风格Report：format 输出用 | 分隔的对齐表格。
# 3. 思考：模板方法与第249课“归并排序的拆-合骨架”有什么神似之处？
# 4. 思考：什么时候用模板方法，什么时候用策略？
