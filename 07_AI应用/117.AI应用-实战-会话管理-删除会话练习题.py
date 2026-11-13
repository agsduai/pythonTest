# ===== 第117课：AI应用-实战-会话管理-删除会话 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 用 dict.pop(session_id, None) 从会话字典中删除指定会话
#   - 删除后立即调用 save_sessions() 同步到 JSON 文件
#   - 删除当前会话后，自动切换到剩余会话或置空
#   - 每个删除按钮使用唯一 key，避免组件冲突
# 依赖：pip install streamlit

import json
import os

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


if "sessions" not in st.session_state:
    st.session_state.sessions = load_sessions()
if "current_id" not in st.session_state:
    st.session_state.current_id = next(iter(st.session_state.sessions), None)

with st.sidebar:
    st.title("AI 助手")
    st.subheader("历史会话")
    # list() 复制一份，避免遍历时修改字典导致报错
    for session_id, session in list(st.session_state.sessions.items()):
        col_view, col_delete = st.columns([4, 1])
        with col_view:
            if st.button(session["title"], key=f"view_{session_id}", use_container_width=True):
                st.session_state.current_id = session_id
                st.rerun()
        with col_delete:
            if st.button("🗑", key=f"delete_{session_id}"):
                st.session_state.sessions.pop(session_id, None)
                save_sessions()
                # 删除的是当前会话时，切换到其他会话或置空
                if st.session_state.current_id == session_id:
                    st.session_state.current_id = next(iter(st.session_state.sessions), None)
                st.rerun()

if st.session_state.current_id is None:
    st.info("暂无会话，请先新建一个会话。")
else:
    current = st.session_state.sessions[st.session_state.current_id]
    st.caption(f"当前会话：{current['title']}")
    for message in current["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("请输入你的问题")
    if prompt:
        current["messages"].append({"role": "user", "content": prompt})
        st.chat_message("user").markdown(prompt)
        save_sessions()

# ===== 练习题 =====
# 1. 删除当前会话，观察页面是否自动切换到另一个会话。
# 2. 删除全部会话，确认页面显示“暂无会话”而不是报错。
# 3. 给删除操作增加二次确认（例如 st.checkbox 或 st.dialog）。
