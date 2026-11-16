# ===== 第628课：终端与命令行应用-子命令与配置优先级 =====
# 知识点：
#   - add_subparsers(dest="command", required=True)：git/commit、docker/run 式子命令
#   - 每个子解析器有自己的参数集；用 set_defaults(func=...) 绑定处理函数
#   - 配置优先级：命令行 > 环境变量 > 配置文件 > 代码默认值
#   - 用 os.environ（可注入字典）与 json 配置文件演示分层覆盖，避免真实全局状态
#   - 合并配置时逐层 update，最后一层生效；None 表示「未设置」要跳过
#   - 子命令让一个入口文件承载多个相关工具，比散落多个脚本更好维护
# 依赖：无（标准库）
import argparse
import json
import os
import tempfile
from pathlib import Path


def load_config(path, env, cli):
    """按 默认值 -> 文件 -> 环境变量 -> 命令行 逐层覆盖。"""
    cfg = {"host": "localhost", "port": 8080, "debug": False, "workers": 4}
    if path and Path(path).exists():
        cfg.update(json.loads(Path(path).read_text("utf-8")))
    mapping = {"APP_HOST": "host", "APP_PORT": "port",
               "APP_DEBUG": "debug", "APP_WORKERS": "workers"}
    for key, name in mapping.items():
        if key in env and env[key] != "":
            raw = env[key]
            if name in ("port", "workers"):
                cfg[name] = int(raw)
            elif name == "debug":
                cfg[name] = raw.lower() in ("1", "true", "yes", "on")
            else:
                cfg[name] = raw
    for key, value in cli.items():
        if value is not None:
            cfg[key] = value
    return cfg


def cmd_serve(args):
    cfg = load_config(args.config, args.env, {"host": args.host, "port": args.port,
                                             "debug": None, "workers": None})
    print(f"  [serve] 启动服务 {cfg['host']}:{cfg['port']} "
          f"workers={cfg['workers']} debug={cfg['debug']}")


def cmd_init(args):
    print(f"  [init] 初始化项目 {args.name!r}，模板={args.template}，强制={args.force}")


def cmd_status(args):
    print(f"  [status] 详细程度={args.verbose}，输出格式={args.format}")


def build_parser():
    p = argparse.ArgumentParser(prog="tool", description="多子命令 CLI 演示")
    p.add_argument("--config", help="JSON 配置文件路径")
    sub = p.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="启动服务")
    serve.add_argument("--host")
    serve.add_argument("--port", type=int)
    serve.set_defaults(func=cmd_serve, env={})

    init = sub.add_parser("init", help="初始化项目")
    init.add_argument("name")
    init.add_argument("--template", choices=("basic", "web", "cli"), default="basic")
    init.add_argument("-f", "--force", action="store_true")
    init.set_defaults(func=cmd_init, env={})

    status = sub.add_parser("status", help="查看状态")
    status.add_argument("-v", action="count", default=0, dest="verbose")
    status.add_argument("--format", choices=("text", "json"), default="text")
    status.set_defaults(func=cmd_status, env={})
    return p


def dispatch(argv, env=None):
    args = build_parser().parse_args(argv)
    args.env = env if env is not None else dict(os.environ)
    return args.func(args)


print("== 三个子命令 ==")
for argv in (
    ["init", "myapp", "--template", "web", "-f"],
    ["status", "-vv", "--format", "json"],
    ["serve", "--host", "0.0.0.0", "--port", "9000"],
):
    print(f"\n$ tool {' '.join(argv)}")
    dispatch(argv, env={})

print("\n== 配置优先级演示 ==")
with tempfile.TemporaryDirectory() as tmp:
    cfg = Path(tmp) / "app.json"
    cfg.write_text(json.dumps({"host": "file.example", "port": 7000, "workers": 8}), "utf-8")
    layers = [
        ("仅默认值", ["--config", str(cfg), "serve"], {}),
        ("文件覆盖默认值", ["--config", str(cfg), "serve"], {}),
        ("环境变量覆盖文件", ["--config", str(cfg), "serve"],
         {"APP_PORT": "6000", "APP_DEBUG": "true"}),
        ("命令行覆盖一切", ["--config", str(cfg), "serve", "--port", "5000"],
         {"APP_PORT": "6000", "APP_DEBUG": "true"}),
    ]
    # 单独打印每层的合并结果，便于观察
    for label, argv, env in layers:
        parsed = build_parser().parse_args(argv)
        merged = load_config(parsed.config, env,
                             {"host": parsed.host, "port": parsed.port,
                              "debug": None, "workers": None})
        print(f"  {label:<16}: host={merged['host']:<14} port={merged['port']:<5} "
              f"workers={merged['workers']} debug={merged['debug']}")

print("\n== 子命令帮助 ==")
for line in build_parser().format_help().splitlines()[:14]:
    print("  " + line)

print("\n== 工程要点 ==")
for line in [
    "required=True（Python 3.7+）避免没给子命令时静默什么都不做",
    "env 用参数注入而非直接读 os.environ，单测可以完全隔离环境变量",
    "每个子命令绑定 func，主流程只负责 dispatch，扩展新命令不改主逻辑",
    "敏感配置（密码/密钥）不要写进配置文件，走环境变量或密钥管理服务",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 增加 config 子命令，打印当前合并后的完整配置（隐藏敏感字段）。
# 2. 实现 --env-file 读取 KEY=VALUE 文本文件，并插入到「文件之后、环境变量之前」。
# 3. 给子命令加通用的 --verbose，用父解析器参数或 parents= 复用。
# 4. 思考：为什么「命令行 > 环境变量 > 文件 > 默认值」这个顺序适合容器化部署？
