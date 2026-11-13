# ===== 第096课：AI应用-大模型调用-会话记忆方案 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 大模型 API 本身是无状态的：每次请求都像第一次见面，不会自动记住历史
#   - 会话记忆的本质：客户端保存历史消息，每次调用时把完整 messages 一起发送
#   - 三种角色：system 设定助手身份，user 是用户输入，assistant 是模型回答
#   - 上下文窗口有限，历史越长消耗 token 越多，需要裁剪或摘要
#   - 常用策略：保留 system + 最近 N 轮对话；更早内容做摘要；限制消息总长度
#   - 实际项目中还会把会话保存到 JSON 文件或数据库，下次启动再加载
# 依赖：无（仅使用标准库）

class ChatMemory:
    """一个最简单的会话记忆容器，可生成发给大模型的 messages 列表。"""

    def __init__(self, system_prompt="你是一个乐于助人的中文助手。", max_turns=5):
        self.system_prompt = system_prompt
        self.max_turns = max_turns   # 最多保留最近多少轮问答
        self.messages = [{"role": "system", "content": system_prompt}]

    def add_user(self, content):
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, content):
        self.messages.append({"role": "assistant", "content": content})

    def get_messages(self):
        """返回 system 消息 + 最近 max_turns 轮对话。"""
        history = self.messages[1:]                  # 去掉 system 消息
        recent = history[-self.max_turns * 2:]       # 一轮包含 user 和 assistant
        return [self.messages[0]] + recent

    def clear(self):
        """清空历史，但保留 system 设定。"""
        self.messages = [{"role": "system", "content": self.system_prompt}]


if __name__ == "__main__":
    memory = ChatMemory(system_prompt="你是课程助手，回答要简洁。", max_turns=2)
    memory.add_user("我叫小明。")
    memory.add_assistant("你好，小明！")
    memory.add_user("我在学习 Python。")
    memory.add_assistant("很好，坚持练习就会进步。")
    memory.add_user("我叫什么名字？")

    # 请求大模型时，把 get_messages() 的结果放进 payload["messages"]
    for message in memory.get_messages():
        print(f"{message['role']}: {message['content']}")
    print(f"当前保留消息数：{len(memory.get_messages())}")

# ===== 练习题 =====
# 1. 把 max_turns 改为 1，观察历史消息如何被裁剪，并说明 system 为什么必须保留。
# 2. 为 ChatMemory 增加按字符总数裁剪的方法，超过上限时从最旧的非 system 消息删起。
# 3. 自测：大模型服务端会记住上一次对话吗？会话记忆应该由谁负责？
