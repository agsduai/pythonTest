# ===== 第546课：元编程与插件系统-综合案例-插件化数据管道 =====
# 知识点：
#   - 综合运用：__init_subclass__/注册表（540）+ 动态发现（544）
#     + 动态导入（545）+ 描述符校验（542）
#   - 核心（Pipeline）只负责调度，具体处理由插件完成
#   - 插件约定：name、order、process(records) -> records
#   - 配置决定启用哪些插件与顺序；新增插件不改核心代码
#   - 插件异常隔离：单个插件失败时记录并跳过
#   - 这是数据清洗/ETL/规则引擎的常见架构
# 依赖：无（importlib 标准库）

import importlib.util
import tempfile
from pathlib import Path
from typing import Protocol


class Stage(Protocol):
    name: str
    order: int

    def process(self, records: list[dict]) -> list[dict]: ...


class Pipeline:
    def __init__(self, stages: list[Stage] | None = None):
        self.stages = stages or []
        self.errors = []

    def add(self, stage: Stage):
        self.stages.append(stage)
        self.stages.sort(key=lambda s: s.order)
        return self

    def run(self, records: list[dict]) -> tuple[list[dict], list[str]]:
        data = [dict(r) for r in records]
        log = []
        for stage in self.stages:
            try:
                before = len(data)
                data = stage.process(data)
                log.append(f"{stage.name}: {before} → {len(data)} 条")
            except Exception as exc:
                self.errors.append((stage.name, str(exc)))
                log.append(f"{stage.name}: 失败（{type(exc).__name__}），跳过")
        return data, log


def load_stages(directory: Path) -> list[Stage]:
    stages = []
    for path in sorted(Path(directory).glob("*.py")):
        try:
            spec = importlib.util.spec_from_file_location(f"stage_{path.stem}", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            stage = getattr(module, "STAGE", None)
            if stage is None or not hasattr(stage, "process"):
                continue
            stages.append(stage)
        except Exception as exc:
            print(f"  [跳过] {path.name}: {exc}")
    return stages


# ---------------- 插件定义 ----------------
CLEAN = '''
class Clean:
    name = "clean"
    order = 10
    def process(self, records):
        for r in records:
            r["name"] = str(r.get("name", "")).strip()
        return records
STAGE = Clean()
'''

FILTER = '''
class Filter:
    name = "filter"
    order = 20
    def process(self, records):
        return [r for r in records if r.get("name") and r.get("amount", 0) > 0]
STAGE = Filter()
'''

TAX = '''
class Tax:
    name = "tax"
    order = 30
    def process(self, records):
        for r in records:
            r["amount"] = round(r["amount"] * 1.1, 2)
        return records
STAGE = Tax()
'''

BROKEN = '''
class Broken:
    name = "broken"
    order = 25
    def process(self, records):
        raise RuntimeError("故意失败")
STAGE = Broken()
'''

with tempfile.TemporaryDirectory() as tmp:
    plugin_dir = Path(tmp) / "stages"
    plugin_dir.mkdir()
    for filename, code in (
        ("10_clean.py", CLEAN),
        ("20_filter.py", FILTER),
        ("25_broken.py", BROKEN),
        ("30_tax.py", TAX),
    ):
        (plugin_dir / filename).write_text(code, encoding="utf-8")

    print("== 扫描插件 ==")
    stages = load_stages(plugin_dir)
    print("  加载顺序：", [(s.order, s.name) for s in sorted(stages, key=lambda x: x.order)])

    pipeline = Pipeline().add(stages[0])
    for stage in stages[1:]:
        pipeline.add(stage)

    records = [
        {"name": " 键盘 ", "amount": 199},
        {"name": "", "amount": 50},          # 空名字，应被过滤
        {"name": "鼠标", "amount": -10},      # 负金额，应被过滤
        {"name": "显示器", "amount": 1299},
    ]

    print("\n== 第一次运行 ==")
    result, log = pipeline.run(records)
    for line in log:
        print("  ", line)
    print("  结果：", result)
    print("  总金额：", sum(r["amount"] for r in result))
    print("  隔离的错误：", pipeline.errors)

    # ---------------- 新增插件，不改核心 ----------------
    print("\n== 新增折扣插件（order=40）==")
    (plugin_dir / "40_discount.py").write_text(
        'class Discount:\n'
        '    name = "discount"\n'
        '    order = 40\n'
        '    def process(self, records):\n'
        '        for r in records:\n'
        '            if r["amount"] > 1000:\n'
        '                r["amount"] = round(r["amount"] * 0.9, 2)\n'
        '        return records\n'
        'STAGE = Discount()\n',
        encoding="utf-8",
    )
    stages2 = load_stages(plugin_dir)
    pipeline2 = Pipeline()
    for stage in stages2:
        pipeline2.add(stage)
    result2, log2 = pipeline2.run(records)
    print("  执行日志：")
    for line in log2:
        print("   ", line)
    print("  结果：", result2)
    print("  总金额：", sum(r["amount"] for r in result2))

# ---------------- 架构说明 ----------------
print("\n== 架构说明 ==")
for item in [
    "核心 Pipeline 只依赖 Stage 协议，不认识具体插件",
    "新增插件 = 新增一个文件，重启扫描即可",
    "order 控制顺序；name 用于日志与配置",
    "插件异常被隔离，主流程继续（第448课死信思想）",
    "生产可把插件目录换成 entry_points（已安装包自动发现）",
    "安全：只加载可信插件目录，动态执行等于执行任意代码",
]:
    print("  -", item)

# ---- 可扩展方向 ----
print("\n== 可扩展方向 ==")
for item in [
    "插件配置（启用/禁用、参数）",
    "插件依赖与拓扑排序",
    "每个插件的输入/输出 schema 校验",
    "插件执行耗时与指标（第417课）",
    "插件版本与兼容性检查（第502课）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 增加一个“去重”插件（按 name 去重）。
# 2. 给 Pipeline 增加“只运行配置中启用的插件”。
# 3. 增加插件级超时控制（第444课），防止单个插件卡死。
# 4. 思考：插件化架构的代价是什么？什么项目不该插件化？
