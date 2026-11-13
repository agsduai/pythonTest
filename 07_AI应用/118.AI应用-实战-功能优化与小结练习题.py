# ===== 第118课：AI应用-实战-功能优化与小结 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 用 try/except 处理 API 调用失败、文件读写失败
#   - 用 st.spinner 展示等待状态，提升使用体验
#   - 自动用首条问题生成会话标题，并更新 updated_at
#   - 对空会话、空输入等边界情况做保护
# 依赖：pip install streamlit openai

import json
from datetime import datetime

import streamlit as st
from openai import OpenAI

client = OpenAI(api_key="sk-请替换为你的DeepSeek密钥", base_url="https://api.deepseek.com")
DATA_FILE = "sessions.json"

def load_sessions():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def save_sessions(sessions):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
    except OSError as error:
        st.error(f"保存会话失败：{error}")


if "sessions" not in st.session_state:
    st.session_state.sessions = load_sessions()
    if not st.session_state.sessions:
        st.session_state.sessions["demo"] = {
            "title": "新会话", "messages": [], "updated_at": "",
        }
    st.session_state.current_id = next(iter(st.session_state.sessions))

current = st.session_state.sessions[st.session_state.current_id]
st.title("对话")
st.caption(f"当前会话：{current['title']}，共 {len(current['messages'])} 条消息")
for message in current["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("请输入你的问题")
if prompt:
    current["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.spinner("AI 正在思考..."):
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=current["messages"],
            )
        answer = response.choices[0].message.content
    except Exception as error:
        answer = f"调用失败，请检查网络或密钥：{error}"

    current["messages"].append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)

    if current["title"] == "新会话" and prompt.strip():
        current["title"] = prompt[:20]
    current["updated_at"] = datetime.now().isoformat(timespec="seconds")
    save_sessions(st.session_state.sessions)
    st.rerun()

# ===== 练习题 =====
# 1. 断开网络后提问，确认错误提示出现且程序不会崩溃。
# 2. 把 save_sessions 中的 OSError 改成捕获所有异常，比较两种写法。
# 3. 为“清空当前会话”增加二次确认，避免误点丢失对话。
