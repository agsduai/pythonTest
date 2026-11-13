# ===== 第105课：AI应用-实战-界面消息展示 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 用 st.session_state 保存对话消息，页面重跑不丢失
#   - 消息使用 {"role": ..., "content": ...} 结构保存
#   - 遍历消息列表，用 st.chat_message 按角色渲染气泡
#   - st.markdown 支持在气泡中显示 Markdown 文本
# 依赖：pip install streamlit

import streamlit as st

st.set_page_config(page_title="消息展示", page_icon="💬")
st.title("AI 智能助手")
st.caption("第 105 课：界面消息展示")

# session_state 中的数据在页面重跑后仍然保留
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "你好，我是 AI 助手，请问有什么可以帮你？"}
    ]

# 遍历历史消息，按角色渲染成不同的聊天气泡
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 底部输入框；用户回车后返回输入内容
prompt = st.chat_input("请输入你的问题")

if prompt:
    # 1. 保存并展示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. 用固定文本模拟 AI 回复，后续替换为真实大模型调用
    reply = f"我收到了你的问题：{prompt}"
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)

# ===== 练习题 =====
# 1. 给 assistant 气泡设置头像，例如 st.chat_message("assistant", avatar="🤖")。
# 2. 在页面顶部增加“清空对话”按钮，点击后把 messages 重置为初始列表。
# 3. 发送包含 **加粗** 和 `代码` 的文本，验证 Markdown 渲染效果。
