# ===== 第106课：AI应用-实战-会话记忆问题 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 大模型 API 本身是无状态的，不会自动记住上一轮对话
#   - 会话记忆需要在客户端维护 messages 历史列表
#   - 每次请求都把完整历史发给模型，模型才能理解上下文
#   - 历史越长消耗的 token 越多，后续需要做长度控制
# 依赖：pip install streamlit openai

import streamlit as st
from openai import OpenAI

# 占位密钥：请从环境变量读取，不要把真实密钥提交到代码仓库
client = OpenAI(
    api_key="sk-请替换为你的DeepSeek密钥",
    base_url="https://api.deepseek.com",
)

st.title("AI 智能助手")
st.caption("第 106 课：会话记忆问题")

# messages 列表就是模型的“记忆”，必须放在 session_state 中跨页面重跑保存
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("请输入你的问题")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 关键：把完整的 messages 历史一起发送，而不是只发当前这一句
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=st.session_state.messages,
    )
    answer = response.choices[0].message.content

    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)

# ===== 练习题 =====
# 1. 先问“我叫小明”，再问“我叫什么”，观察模型是否能答对。
# 2. 在请求前打印 len(st.session_state.messages)，理解历史消息如何增长。
# 3. 只发送最后一条用户消息，对比模型是否还能记住上文。
