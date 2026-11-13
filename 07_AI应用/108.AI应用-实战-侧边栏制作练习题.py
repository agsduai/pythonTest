# ===== 第108课：AI应用-实战-侧边栏制作 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - st.sidebar 创建侧边栏，with 语句集中放置侧边栏组件
#   - st.button 新建会话、st.selectbox 选择模型、st.slider 调参数
#   - st.divider 分隔区块，st.caption 显示辅助说明
#   - 主区域与侧边栏分工：侧边栏放全局设置，主区域放对话
# 依赖：pip install streamlit

import streamlit as st

st.set_page_config(page_title="AI 智能助手", page_icon="🤖", layout="wide")

# ===== 侧边栏 =====
with st.sidebar:
    st.title("AI 助手")
    # 新建会话按钮：本课只做界面，逻辑在会话管理章节实现
    st.button("➕ 新建会话", use_container_width=True)
    st.divider()

    st.subheader("历史会话")
    st.caption("暂无历史会话")

    st.divider()
    # 模型与生成参数放在侧边栏，方便随时调整
    model = st.selectbox("模型", ["deepseek-chat", "deepseek-reasoner"])
    temperature = st.slider(
        "温度", min_value=0.0, max_value=1.0, value=0.7, step=0.1
    )
    st.caption(f"当前模型：{model}，温度：{temperature}")

# ===== 主区域 =====
st.title("对话")
st.chat_message("assistant").markdown("你好，我是 AI 助手。")

prompt = st.chat_input("请输入你的问题")
if prompt:
    st.chat_message("user").markdown(prompt)

# ===== 练习题 =====
# 1. 在侧边栏增加“清空对话”按钮，并放在“新建会话”下方。
# 2. 用 st.radio 让用户在 deepseek-chat 和 deepseek-reasoner 之间选择。
# 3. 给温度滑块增加 help 参数，解释“值越大回答越发散”。
