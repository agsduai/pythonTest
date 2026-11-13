# ===== 第185课：感恩同行-后会有期 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 回顾课程主线：语法基础 → 数据容器 → 函数 → 面向对象 → AI 应用 → Web
#   - 把项目经验沉淀为可复用的开发流程
#   - 制定持续学习计划，避免“学完就忘”
#   - 保持好奇、动手实践、善用 AI 工具
# 依赖：无

COURSE_MAP = {
    "语法基础": ["变量与数据类型", "流程控制", "数据容器"],
    "工程能力": ["函数", "模块与包", "面向对象", "异常处理"],
    "AI 应用": ["大模型调用", "Streamlit", "FastAPI"],
    "数据与自动化": ["网络机器人", "Pandas", "Matplotlib"],
}


def count_topics(course_map: dict[str, list[str]]) -> int:
    """统计课程涵盖的知识点总数。"""
    return sum(len(topics) for topics in course_map.values())


def build_plan(days: int = 30) -> list[str]:
    """生成一个可执行的复习计划，每天一个主题。"""
    topics = [topic for topics in COURSE_MAP.values() for topic in topics]
    plan = []
    for index in range(days):
        topic = topics[index % len(topics)]
        plan.append(f"第 {index + 1} 天：复习 {topic}")
    return plan


def print_summary() -> None:
    """打印课程回顾与临别寄语。"""
    print("=" * 40)
    print("课程回顾")
    print("=" * 40)
    for chapter, topics in COURSE_MAP.items():
        print(f"{chapter}：{'、'.join(topics)}")
    print(f"\n共涵盖 {count_topics(COURSE_MAP)} 个知识点")
    print("感谢一路同行，愿你保持热爱，后会有期！")


if __name__ == "__main__":
    print_summary()
    print("\n30 天复习计划（前 5 天）")
    for item in build_plan(30)[:5]:
        print(item)

# ===== 练习题 =====
# 1. 用三句话写下本课程最大的三个收获，并保存到学习笔记。
# 2. 选择一个做过的小项目，补齐 README、依赖文件和运行说明。
# 3. 制定 30 天计划：复习、刷题、做项目各占多少时间？
