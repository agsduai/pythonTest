# ===== 第397课：配置与序列化-INI与configparser =====
# 知识点：
#   - INI：最老牌的配置文件格式，分节 [section]、键值 key = value
#   - ConfigParser：read/write/get/getint/getboolean；[DEFAULT] 是全局默认
#   - interpolation=None：关闭 % 插值，避免密码里的 % 被误解析
#   - 类型只有字符串：数字/布尔要显式转换（getint/getboolean）
#   - 适合：小型工具的本地配置；复杂嵌套建议 JSON/TOML（后续课）
import configparser
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    ini_path = Path(tmp) / "app.ini"

    # ---- 写：分节 + DEFAULT 默认值 ----
    cfg = configparser.ConfigParser(interpolation=None)
    cfg["DEFAULT"] = {"timeout": "30", "encoding": "utf-8"}   # 所有节共享
    cfg["server"] = {
        "host": "127.0.0.1",
        "port": "8080",
        "debug": "true",
    }
    cfg["database"] = {"url": "sqlite:///app.db", "pool": "5"}

    with open(ini_path, "w", encoding="utf-8") as f:
        cfg.write(f)

    print("== 生成的 INI ==")
    print(ini_path.read_text(encoding="utf-8"))

    # ---- 读 ----
    loaded = configparser.ConfigParser(interpolation=None)
    loaded.read(ini_path, encoding="utf-8")

    print("所有节：", loaded.sections())          # DEFAULT 不列出
    print("主机：", loaded["server"]["host"])
    print("端口（int）：", loaded.getint("server", "port"))
    print("调试（bool）：", loaded.getboolean("server", "debug"))
    print("超时（继承自 DEFAULT）：", loaded["server"]["timeout"])
    print("数据库节全部键值：", dict(loaded["database"]))

    # ---- 运行时修改并写回 ----
    loaded["server"]["port"] = "9090"
    with open(ini_path, "w", encoding="utf-8") as f:
        loaded.write(f)
    reread = configparser.ConfigParser(interpolation=None)
    reread.read(ini_path, encoding="utf-8")
    print("改端口后重新读取：", reread["server"]["port"])

    # ---- 缺节/缺键的容错 ----
    print("不存在的键（fallback）：", loaded.get("server", "missing", fallback="<默认>"))
    try:
        loaded["not_exist"]
    except KeyError as exc:
        print("访问不存在的节：", exc)

# 注意事项：
#   - 用默认 interpolation 时，值里的 % 必须写成 %% 或用 interpolation=None
#   - 键名不区分大小写（会被统一小写）
#   - 不支持嵌套结构，深层配置请用 JSON/TOML

# ===== 练习题 =====
# 1. 增加 [logging] 节（level、file），用 getint/getboolean 读取。
# 2. 写一个函数 load_ini(path) → dict，把每节转成普通字典。
# 3. 验证：值写成 100% 时，默认插值模式会报什么错？
