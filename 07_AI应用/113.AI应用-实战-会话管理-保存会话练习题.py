# ===== 第113课：AI应用-实战-会话管理-保存会话 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 会话数据采用“会话 id → 会话信息”的字典结构
#   - json.dump 把全部会话写入 sessions.json
#   - 每轮回答后立即保存，页面刷新也不会丢失
#   - 文件不存在时返回空字典，避免读取时报错
# 依赖：pip install streamlit

import json
import os
from datetime import datetime

import streamlit as st

DATA_FILE = "sessions.json"


def load_sessions():
    """读取本地 JSON 文件；文件不存在时返回空字典"""
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_sessions(sessions):
    """把全部会话写回 JSON 文件"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)


# 首次进入页面时加载历史数据，并准备一个当前会话
if "sessions" not in st.session_state:
    st.session_state.sessions = load_sessions()
if "current_id" not in st.session_state:
    st.session_state.current_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    st.session_state.sessions[st.session_state.current_id] = {
        "title": "新会话",
        "messages": [],
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }

current = st.session_state.sessions[st.session_state.current_id]

st.title("AI 智能助手")
for message in current["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("请输入你的问题")
if prompt:
    current["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 本课用固定文本模拟回复，重点是在回答后立即保存
    answer = f"收到你的问题：{prompt}"
    current["messages"].append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)

    if current["title"] == "新会话":
        current["title"] = prompt[:20]  # 用首条问题生成标题
    current["updated_at"] = datetime.now().isoformat(timespec="seconds")
    save_sessions(st.session_state.sessions)  # 关键：写入 JSON 文件

# ===== 练习题 =====
# 1. 连续发送两轮消息，打开 sessions.json 观察文件内容的变化。
# 2. 刷新页面后确认消息仍在，理解“保存”和 session_state 的区别。
# 3. 给 save_sessions 增加 try/except，写入失败时用 st.error 提示。
