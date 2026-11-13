# ===== 第089课：AI应用-大模型部署-方案 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 方案一：调用官方开放 API（DeepSeek、通义千问等），开箱即用
#   - 方案二：本地部署（Ollama、LM Studio），数据留在本机，可离线运行
#   - 方案三：云服务器自建推理服务（vLLM 等），适合团队与高并发
#   - 选型维度：成本、数据隐私、网络条件、硬件配置、模型效果、运维能力
#   - 学习阶段建议：先用官方 API 跑通流程，再尝试 Ollama 本地模型
# 依赖：无（本课为方案对比，仅使用标准库）

# 三种部署方案的关键信息对比
DEPLOY_OPTIONS = {
    "官方API": {
        "成本": "按量付费，无需买显卡",
        "隐私": "数据会发送到服务商",
        "网络": "必须联网",
        "效果": "通常最好，可选用大参数模型",
        "运维": "服务商负责",
    },
    "Ollama本地部署": {
        "成本": "电费 + 硬件，无调用费",
        "隐私": "数据不出本机",
        "网络": "可离线使用",
        "效果": "受本机内存/显存限制",
        "运维": "自己安装和升级模型",
    },
    "云服务器自建": {
        "成本": "服务器租金较高",
        "隐私": "数据在自己租用的服务器上",
        "网络": "需要公网与安全配置",
        "效果": "可选较大模型，依赖显卡",
        "运维": "需要自己维护推理框架",
    },
}


def show_comparison():
    """逐项打印三种方案的对比信息。"""
    for name, info in DEPLOY_OPTIONS.items():
        print(f"\n【{name}】")
        for key, value in info.items():
            print(f"  {key}：{value}")


def recommend(need_offline, need_privacy, has_gpu, low_budget):
    """根据简单条件给出学习阶段的方案建议（仅作演示）。"""
    if need_offline or (need_privacy and has_gpu):
        return "Ollama本地部署"
    if need_privacy and not low_budget:
        return "云服务器自建"
    return "官方API"


if __name__ == "__main__":
    show_comparison()
    print("\n" + "=" * 40)
    # 模拟一个“需要离线、没有显卡、预算有限”的学习者
    choice = recommend(need_offline=True, need_privacy=True,
                       has_gpu=False, low_budget=True)
    print(f"推荐方案：{choice}")

# ===== 练习题 =====
# 1. 补全 DEPLOY_OPTIONS，为每种方案再增加“适合人群”一列并打印。
# 2. 修改 recommend 函数，让“高并发”场景优先推荐云服务器自建方案。
# 3. 自测：某公司要求合同数据绝不能离开内网，应优先选哪种方案？为什么？
