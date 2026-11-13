# ===== 第107课：AI应用-实战-流式输出 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 请求参数 stream=True 开启流式返回
#   - 逐块读取 chunk.choices[0].delta.content
#   - 用生成器 + st.write_stream 实现打字机效果
#   - 流式结束后再把完整回答写入会话历史
# 依赖：pip install streamlit openai

import streamlit as st
from openai import OpenAI

# 占位密钥：真实密钥请放在环境变量中，不要写进代码
client = OpenAI(
    api_key="sk-请替换为你的DeepSeek密钥",
    base_url="https://api.deepseek.com",
)

st.title("AI 智能助手")
st.caption("第 107 课：流式输出")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def stream_reply(messages):
    """调用大模型，并以生成器方式逐块返回文本"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=True,  # 开启流式输出
    )
    for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:  # 结束块可能没有内容，需要判断
            yield delta


prompt = st.chat_input("请输入你的问题")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # st.write_stream 会消费生成器并逐字显示
        answer = st.write_stream(stream_reply(st.session_state.messages))

    st.session_state.messages.append({"role": "assistant", "content": answer})

# ===== 练习题 =====
# 1. 把 stream=True 改为 False，对比“一次性出现”和“逐字出现”的体验。
# 2. 用 st.empty() 创建占位符，手动循环拼接文本并调用 placeholder.markdown。
# 3. 在流式输出结束后用 st.toast("回答完成") 给出提示。
