# ===== 第116课：AI应用-实战-会话管理-加载会话 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 用 selectbox 展示历史会话，format_func 显示会话标题
#   - 选择变化时把 current_id 切换为对应会话 id
#   - 加载会话就是把该会话的 messages 重新渲染到主区域
#   - 切换后 st.rerun() 让页面立即显示新会话内容
# 依赖：pip install streamlit

import json
import os

import streamlit as st

DATA_FILE = "sessions.json"


def load_sessions():
    """读取 sessions.json；文件不存在时返回空字典"""
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


if "sessions" not in st.session_state:
    st.session_state.sessions = load_sessions()
    # 没有历史文件时用演示数据，方便观察加载效果
    if not st.session_state.sessions:
        st.session_state.sessions = {
            "s1": {"title": "Python 学习", "messages": [{"role": "assistant", "content": "你好"}]},
            "s2": {"title": "AI 问答", "messages": []},
        }
    st.session_state.current_id = next(iter(st.session_state.sessions))

session_ids = list(st.session_state.sessions.keys())
if st.session_state.get("current_id") not in session_ids:
    st.session_state.current_id = session_ids[0]

with st.sidebar:
    st.title("AI 助手")
    st.subheader("历史会话")
    # format_func 决定下拉框中显示的文字
    selected_id = st.selectbox(
        "选择要加载的会话",
        session_ids,
        index=session_ids.index(st.session_state.current_id),
        format_func=lambda sid: st.session_state.sessions[sid]["title"],
    )
    # 选择发生变化时切换当前会话
    if selected_id != st.session_state.current_id:
        st.session_state.current_id = selected_id
        st.rerun()

current = st.session_state.sessions[st.session_state.current_id]
st.title(current["title"])
st.caption(f"共 {len(current['messages'])} 条消息")

# 加载：遍历该会话的历史消息并渲染
for message in current["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ===== 练习题 =====
# 1. 手动修改 sessions.json 中某个会话的 messages，刷新后观察加载结果。
# 2. 在侧边栏显示每个会话的消息条数，例如“标题（3 条）”。
# 3. 加载会话后把页面标题改成该会话的 title。
