# ===== 第402课：配置与序列化-配置分层与环境变量 =====
# 知识点：
#   - 配置优先级：命令行参数 > 环境变量 > 配置文件 > 代码默认值
#   - 12-Factor App 原则：配置放环境变量，代码不因环境而改
#   - 环境变量是字符串：要按默认值的类型做转换（int/bool）
#   - 敏感信息（密钥/密码）只放环境变量，绝不进代码和仓库（第217课）
#   - 合并策略：逐层 update，高层覆盖低层
import json
import os
import tempfile
from pathlib import Path

# 第 1 层：代码默认值（最低优先级）
DEFAULTS = {
    "host": "127.0.0.1",
    "port": 8000,
    "debug": False,
    "retries": 3,
    "log_level": "INFO",
}


def _cast(raw: str, default_value):
    """按默认值的类型转换环境变量字符串。"""
    if isinstance(default_value, bool):
        return raw.lower() in ("1", "true", "yes", "on")
    if isinstance(default_value, int):
        return int(raw)
    if isinstance(default_value, float):
        return float(raw)
    return raw


def load_config(defaults: dict, file_path: Path | None = None,
                env: dict | None = None, cli: dict | None = None) -> dict:
    """四层合并：defaults < file < env < cli。cli 中 None 表示未指定。"""
    config = dict(defaults)

    # 第 2 层：配置文件
    if file_path and Path(file_path).exists():
        with open(file_path, encoding="utf-8") as f:
            config.update(json.load(f))

    # 第 3 层：环境变量（约定前缀 APP_）
    env = env if env is not None else os.environ
    for key, default_value in defaults.items():
        env_key = f"APP_{key.upper()}"
        if env_key in env:
            config[key] = _cast(env[env_key], default_value)

    # 第 4 层：命令行（最高）
    if cli:
        config.update({k: v for k, v in cli.items() if v is not None})

    return config


with tempfile.TemporaryDirectory() as tmp:
    cfg_file = Path(tmp) / "config.json"
    cfg_file.write_text(json.dumps({"port": 9000, "debug": True, "retries": 5}),
                        encoding="utf-8")

    print("== 只有默认值 ==")
    print(load_config(DEFAULTS, env={}))

    print("\n== + 配置文件（port=9000, debug=True, retries=5）==")
    print(load_config(DEFAULTS, file_path=cfg_file, env={}))

    print("\n== + 环境变量（APP_PORT=9100, APP_DEBUG=0）==")
    env = {"APP_PORT": "9100", "APP_DEBUG": "0", "APP_LOG_LEVEL": "DEBUG"}
    print(load_config(DEFAULTS, file_path=cfg_file, env=env))

    print("\n== + 命令行（--port 9200）==")
    cli = {"port": 9200, "debug": None}          # None 表示“未传”
    final = load_config(DEFAULTS, file_path=cfg_file, env=env, cli=cli)
    print(final)

    print("\n优先级验证：")
    print("  port = 9200（CLI 覆盖了环境变量 9100 与文件 9000）")
    print("  debug = False（环境变量覆盖了文件里的 True）")
    print("  retries = 5（文件覆盖默认值）")
    print("  log_level = DEBUG（环境变量）")

# 敏感信息示例（不要写进代码/仓库）：
#   set APP_DB_PASSWORD=xxxx        （Windows）
#   export APP_DB_PASSWORD=xxxx     （macOS/Linux）
#   代码里只写 os.getenv("APP_DB_PASSWORD")，缺失时明确报错

# ===== 练习题 =====
# 1. 增加 "workers" 配置（int），用环境变量覆盖并验证类型转换。
# 2. 让 env 前缀可配置（如 MYAPP_），改造 load_config。
# 3. 实现 debug 打印：最终配置里把“来自哪一层”标出来。
# 4. 思考：为什么密钥不能放配置文件并提交到 git？（回顾第297课 .gitignore）
