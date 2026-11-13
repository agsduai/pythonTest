# ===== 第258课：设计模式-工厂模式 =====
# 知识点：
#   - 简单工厂：一个函数按参数决定造哪种对象，调用方不用知道类名
#   - 工厂方法：每类产品配一个工厂，新增产品不改旧代码（开闭原则）
#   - 场景：按配置创建导出器/数据库连接/支付渠道
#   - 本质：把“创建对象的 if/elif”收敛到一处

import json
from abc import ABC, abstractmethod


# ---- 产品抽象 ----
class Exporter(ABC):

    @abstractmethod
    def export(self, data) -> str: ...


class JsonExporter(Exporter):

    def export(self, data):
        return json.dumps(data, ensure_ascii=False, indent=2)


class CsvExporter(Exporter):

    def export(self, data):
        return "\n".join(f"{k},{v}" for k, v in data.items())


# ---- 简单工厂：注册表 + 一个创建函数 ----
EXPORTERS = {"json": JsonExporter, "csv": CsvExporter}


def create_exporter(kind: str) -> Exporter:
    cls = EXPORTERS.get(kind)
    if cls is None:
        raise ValueError(f"不支持的导出类型：{kind}（可选 {'/'.join(EXPORTERS)}）")
    return cls()


data = {"name": "小明", "score": 92}
print(create_exporter("json").export(data))
print(create_exporter("csv").export(data))


# ---- 工厂方法：产品与工厂一一对应 ----
class ExporterFactory(ABC):

    @abstractmethod
    def create(self) -> Exporter: ...


class JsonFactory(ExporterFactory):

    def create(self):
        return JsonExporter()


class CsvFactory(ExporterFactory):

    def create(self):
        return CsvExporter()


def run_report(factory: ExporterFactory, data):
    """调用方只依赖抽象工厂，具体产品由工厂决定。"""
    return factory.create().export(data)


print(run_report(JsonFactory(), data))
print(run_report(CsvFactory(), data))

# ===== 练习题 =====
# 1. 给简单工厂新增 XmlExporter（手工拼 <name>92</name> 风格）。
# 2. 给对应新增 XmlFactory，验证 run_report 依旧不用改。
# 3. 把第13课的 sqlite 连接创建改成 create_conn(kind) 工厂函数。
# 4. 思考：什么时候简单工厂就够，什么时候需要工厂方法？
