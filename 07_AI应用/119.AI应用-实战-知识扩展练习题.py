# ===== 第119课：AI应用-实战-知识扩展 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - system 提示词：设定 AI 的角色、回答风格和边界
#   - temperature 控制随机性，max_tokens 限制回答长度
#   - 扩展方向：RAG 知识库、Function Calling、多模态、部署上线
#   - 通过 sidebars 暴露参数，便于对比不同配置的效果
# 依赖：pip install streamlit openai

import streamlit as st
from openai import OpenAI

# 占位密钥：请从环境变量读取，不要提交真实密钥
client = OpenAI(
    api_key="sk-请替换为你的DeepSeek密钥",
    base_url="https://api.deepseek.com",
)

st.title("AI 助手 - 知识扩展")
st.caption("第 119 课：system 提示词与生成参数")

with st.sidebar:
    st.subheader("生成参数")
    temperature = st.slider("temperature", 0.0, 1.5, 0.7, 0.1)
    max_tokens = st.slider("max_tokens", 100, 2000, 800, 100)
    style = st.selectbox("回答风格", ["简洁", "详细", "举例讲解"])

# system 消息放在 messages 最前面，用来设定模型角色
system_prompt = f"你是一名耐心的 Python 助教，请用{style}的方式回答，必要时给出代码示例。"

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

    # 每次请求都临时拼上 system 消息，不写入历史
    request_messages = [{"role": "system", "content": system_prompt}]
    request_messages.extend(st.session_state.messages)

    with st.chat_message("assistant"):
        with st.spinner("生成中..."):
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=request_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        answer = response.choices[0].message.content
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

# ===== 练习题 =====
# 1. 把 temperature 调到 1.5 和 0，分别问同一个问题，比较回答差异。
# 2. 修改 system_prompt，让 AI 只回答 Python 相关问题，拒绝其他话题。
# 3. 查阅资料，说明 RAG 和 Function Calling 分别解决什么问题。
