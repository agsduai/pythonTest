# ===== 第403课：配置与序列化-综合案例-配置中心 =====
# 知识点：
#   - 综合运用：JSON（232/402）+ 类型校验 + 内容指纹热加载（265）+ 环境变量
#   - 配置中心职责：加载 → 校验 → 提供读取 → 变更检测 → 重新加载
#   - 类型校验注意：bool 是 int 的子类，必须用 type(x) is 而非 isinstance
#   - 热加载用“文件内容哈希”判断，比 mtime 可靠（时间戳可能不变）
#   - 非法配置启动即失败（fail fast），不要带病运行
import hashlib
import json
import os
import tempfile
from pathlib import Path

# 配置模式：键 → 期望类型
SCHEMA = {
    "host": str,
    "port": int,
    "debug": bool,
    "retries": int,
    "log_level": str,
}


class ConfigError(Exception):
    pass


class ConfigCenter:

    def __init__(self, path: Path, env: dict | None = None):
        self.path = Path(path)
        self.env = env if env is not None else os.environ
        self.data: dict = {}
        self._fingerprint: str | None = None

    # ---- 加载 + 校验 ----
    def load(self) -> "ConfigCenter":
        if not self.path.exists():
            raise ConfigError(f"配置文件不存在：{self.path}")
        raw_bytes = self.path.read_bytes()
        try:
            raw = json.loads(raw_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ConfigError(f"配置不是合法 JSON：{exc}") from exc

        self._validate(raw)
        self._apply_env(raw)
        self.data = raw
        self._fingerprint = hashlib.sha256(raw_bytes).hexdigest()
        return self

    def _validate(self, raw: dict):
        for key, expected_type in SCHEMA.items():
            if key not in raw:
                raise ConfigError(f"缺少必填配置：{key}")
            # 关键：bool 是 int 子类，必须用 type() 精确判断
            if type(raw[key]) is not expected_type:
                raise ConfigError(
                    f"{key} 类型错误：期望 {expected_type.__name__}，"
                    f"实际 {type(raw[key]).__name__}"
                )
        if not (1 <= raw["port"] <= 65535):
            raise ConfigError(f"port 超出范围：{raw['port']}")
        if not (0 <= raw["retries"] <= 10):
            raise ConfigError(f"retries 超出范围：{raw['retries']}")

    def _apply_env(self, raw: dict):
        """环境变量覆盖（只允许简单类型，按 schema 转换）。"""
        for key in SCHEMA:
            env_key = f"APP_{key.upper()}"
            if env_key not in self.env:
                continue
            value = self.env[env_key]
            if SCHEMA[key] is bool:
                raw[key] = value.lower() in ("1", "true", "yes", "on")
            elif SCHEMA[key] is int:
                try:
                    raw[key] = int(value)
                except ValueError as exc:
                    raise ConfigError(f"{env_key} 不是整数：{value}") from exc
            else:
                raw[key] = value

    # ---- 读取 ----
    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def effective(self) -> dict:
        """返回当前生效配置的副本（用于日志/展示，脱敏需另做）。"""
        return dict(self.data)

    # ---- 热加载：内容哈希变化才重载 ----
    def reload_if_changed(self) -> bool:
        if not self.path.exists():
            return False
        new_fp = hashlib.sha256(self.path.read_bytes()).hexdigest()
        if new_fp == self._fingerprint:
            return False
        print("  检测到配置变更，重新加载……")
        self.load()
        return True


with tempfile.TemporaryDirectory() as tmp:
    cfg_path = Path(tmp) / "app.json"
    cfg_path.write_text(json.dumps({
        "host": "127.0.0.1", "port": 8000, "debug": False,
        "retries": 3, "log_level": "INFO",
    }), encoding="utf-8")

    # ---- 1. 正常加载 ----
    center = ConfigCenter(cfg_path, env={})
    center.load()
    print("== 初始配置 ==")
    for k, v in center.effective().items():
        print(f"  {k:10s} = {v!r} ({type(v).__name__})")

    # ---- 2. 环境变量覆盖 ----
    center_env = ConfigCenter(cfg_path, env={"APP_PORT": "9100", "APP_DEBUG": "true"})
    center_env.load()
    print("\n== 环境变量覆盖后 ==")
    print("  port =", center_env.get("port"), "| debug =", center_env.get("debug"))

    # ---- 3. 热加载 ----
    print("\n== 修改文件 → 热加载 ==")
    cfg_path.write_text(json.dumps({
        "host": "0.0.0.0", "port": 9200, "debug": True,
        "retries": 5, "log_level": "DEBUG",
    }), encoding="utf-8")
    changed = center.reload_if_changed()
    print("  是否重载：", changed, "| 新 port：", center.get("port"))

    print("\n  再次调用（无变化）：", center.reload_if_changed())

    # ---- 4. 非法配置 fail fast ----
    bad_cases = [
        ({"host": "x", "port": "8080", "debug": False, "retries": 3, "log_level": "INFO"},
         "port 写成字符串"),
        ({"host": "x", "port": 8080, "debug": 1, "retries": 3, "log_level": "INFO"},
         "debug 用 1 冒充 bool（bool 是 int 子类）"),
        ({"host": "x", "port": 70000, "debug": False, "retries": 3, "log_level": "INFO"},
         "port 越界"),
        ({"host": "x", "port": 8080, "debug": False, "retries": 3},
         "缺少 log_level"),
    ]
    print("\n== 非法配置拦截 ==")
    for bad, desc in bad_cases:
        cfg_path.write_text(json.dumps(bad), encoding="utf-8")
        try:
            ConfigCenter(cfg_path, env={}).load()
            print(f"  ✗ {desc}：竟然通过了！")
        except ConfigError as exc:
            print(f"  ✓ {desc} → {exc}")

# ===== 练习题 =====
# 1. 给 SCHEMA 增加 "workers"（int，1~64）与 "env"（str，限 dev/prod/test）。
# 2. 实现 get_required(key)：缺失时抛 ConfigError，而不是返回 None。
# 3. 给 effective() 增加脱敏：键名含 password/secret 时输出 ***。
# 4. 思考：配置中心要不要监听文件系统事件？用哈希轮询有什么代价？
