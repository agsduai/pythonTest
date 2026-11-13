# ===== 第109课：AI应用-实战-会话管理-思路分析 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 会话管理要解决的问题：新建、保存、展示列表、加载、删除
#   - 用“会话 id → 会话数据”的字典组织多个会话
#   - 每个会话包含 title、messages、updated_at 三个字段
#   - 所有会话统一保存到一个 JSON 文件，启动时先读取
# 依赖：无（使用 Python 标准库 json、os、datetime）

import json
import os
from datetime import datetime

DATA_FILE = "sessions.json"

# 会话数据结构示例：
# {
#   "20261112120000123456": {
#     "title": "Python 怎么学",
#     "messages": [{"role": "user", "content": "你好"}],
#     "updated_at": "2026-11-12T12:00:00"
#   }
# }
sessions = {}

def new_session():
    """新建会话：用时间戳生成唯一 id，返回会话 id"""
    session_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    sessions[session_id] = {
        "title": "新会话",
        "messages": [],
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    return session_id


def save_sessions():
    """把全部会话写入 JSON 文件"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)


def load_sessions():
    """从 JSON 文件读取会话；文件不存在时返回空字典"""
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    # 启动流程：先加载历史会话，再按需新建
    sessions.update(load_sessions())
    session_id = new_session()
    sessions[session_id]["messages"].append({"role": "user", "content": "你好"})
    save_sessions()
    print("当前会话 id：", session_id)
    print("会话数量：", len(sessions))

# ===== 练习题 =====
# 1. 画出“新建 → 对话 → 保存 → 列表 → 加载 → 删除”的流程图。
# 2. 说明为什么会话 id 使用时间戳，而不是直接用标题。
# 3. 思考：如果两个会话标题相同，列表和删除操作如何区分它们？
