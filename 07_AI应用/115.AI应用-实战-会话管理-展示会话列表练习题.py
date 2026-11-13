# ===== 第115课：AI应用-实战-会话管理-展示会话列表 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 从 sessions.json 读取全部会话，在侧边栏展示
#   - 按 updated_at 倒序排列，最近使用的会话排在最前
#   - 每个会话按钮使用唯一 key，避免组件冲突
#   - 点击按钮切换 current_id 并刷新页面
# 依赖：pip install streamlit

import json
import os

import streamlit as st

DATA_FILE = "sessions.json"


def load_sessions():
    """读取会话文件；不存在或解析失败时返回空字典"""
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


if "sessions" not in st.session_state:
    st.session_state.sessions = load_sessions()
    # 没有文件时用演示数据，方便观察列表效果
    if not st.session_state.sessions:
        st.session_state.sessions = {
            "demo1": {"title": "Python 学习", "messages": [], "updated_at": "2026-11-12T10:00:00"},
            "demo2": {"title": "AI 问答", "messages": [], "updated_at": "2026-11-12T11:00:00"},
        }
    st.session_state.current_id = next(iter(st.session_state.sessions))

with st.sidebar:
    st.title("AI 助手")
    st.subheader("历史会话")
    # 按更新时间倒序，最近使用的会话显示在最上面
    items = sorted(
        st.session_state.sessions.items(),
        key=lambda item: item[1].get("updated_at", ""),
        reverse=True,
    )
    for session_id, session in items:
        # key 必须唯一，否则同名的会话按钮会冲突
        if st.button(session["title"], key=f"open_{session_id}", use_container_width=True):
            st.session_state.current_id = session_id
            st.rerun()

current = st.session_state.sessions[st.session_state.current_id]
st.title("对话")
st.caption(f"当前会话：{current['title']}")
for message in current["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ===== 练习题 =====
# 1. 把 demo1 的 updated_at 改成最新时间，观察它是否排到第一位。
# 2. 给每个会话按钮前加上序号，例如“1. 新会话”。
# 3. 去掉按钮的 key 后运行，观察同名会话时出现什么错误。
