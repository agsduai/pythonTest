# ===== 第114课：AI应用-实战-会话管理-新建会话 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 侧边栏“新建会话”按钮绑定回调逻辑
#   - 用时间戳生成唯一会话 id，避免标题重复
#   - 新会话包含空 messages、默认标题和更新时间
#   - 切换 current_id 后用 st.rerun() 立即刷新页面
# 依赖：pip install streamlit

import json
import os
from datetime import datetime

import streamlit as st

DATA_FILE = "sessions.json"


def load_sessions():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_sessions():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.sessions, f, ensure_ascii=False, indent=2)


def create_session():
    """新建空会话，并把它设为当前会话"""
    session_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    st.session_state.sessions[session_id] = {
        "title": "新会话",
        "messages": [],
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    st.session_state.current_id = session_id
    save_sessions()


if "sessions" not in st.session_state:
    st.session_state.sessions = load_sessions()
if "current_id" not in st.session_state:
    st.session_state.current_id = None

with st.sidebar:
    st.title("AI 助手")
    if st.button("➕ 新建会话", use_container_width=True):
        create_session()
        st.rerun()  # 立即刷新，展示新会话
    st.divider()

st.title("对话")
if st.session_state.current_id is None:
    create_session()  # 首次进入自动创建一个会话
    st.rerun()

current = st.session_state.sessions[st.session_state.current_id]
for message in current["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("请输入你的问题")
if prompt:
    current["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

# ===== 练习题 =====
# 1. 连续点击三次“新建会话”，打印 sessions 的键，观察 id 是否唯一。
# 2. 新建会话后，确认主区域的历史消息被清空。
# 3. 在侧边栏显示“当前会话 id”后 6 位，方便观察切换效果。
