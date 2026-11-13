# ===== 第176课：Web应用-AI汉字谜盒-基础环境准备 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 创建虚拟环境并安装项目依赖
#   - 用 requirements.txt 固定依赖版本
#   - 用 .env 保存密钥，用 python-dotenv 读取
#   - 启动前检查目录、密钥和模型配置
# 依赖：pip install fastapi uvicorn openai python-dotenv

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SESSION_DIR = DATA_DIR / "sessions"
LOG_DIR = BASE_DIR / "logs"
ENV_FILE = BASE_DIR / ".env"


def prepare_dirs() -> None:
    """创建项目运行所需目录，exist_ok=True 避免重复创建报错。"""
    for path in (SESSION_DIR, LOG_DIR):
        path.mkdir(parents=True, exist_ok=True)
        print(f"目录已就绪：{path}")


def load_config() -> dict:
    """读取 .env 中的配置，并做最基本的非空校验。"""
    load_dotenv(ENV_FILE)
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    if not api_key or api_key.startswith("sk-请"):
        raise RuntimeError("未配置 DEEPSEEK_API_KEY，请在 .env 中填写")
    return {"api_key": api_key, "model": model}


def mask_key(key: str) -> str:
    """在日志和终端中只显示脱敏后的密钥。"""
    return f"{key[:6]}****{key[-4:]}" if len(key) > 10 else "****"


if __name__ == "__main__":
    prepare_dirs()
    # .env 示例（不要把真实密钥提交到仓库）：
    # DEEPSEEK_API_KEY=sk-请替换为你的密钥
    # DEEPSEEK_MODEL=deepseek-chat
    try:
        config = load_config()
        print(f"模型：{config['model']}")
        print(f"API Key：{mask_key(config['api_key'])}")
    except RuntimeError as error:
        print(f"环境检查失败：{error}")

# ===== 练习题 =====
# 1. 写出 requirements.txt 中本项目需要的前四个依赖。
# 2. 新建 .env 文件并配置密钥，然后运行本程序检查是否读取成功。
# 3. 增加一项检查：如果模型名称不是 deepseek-chat，则给出提示。
