# ===== 第276课：实用脚本-argparse命令行参数 =====
# 知识点：
#   - argparse：标准库命令行参数解析，自带 --help 与报错提示
#   - 位置参数：必须给；可选参数：-n/--times
#   - type=类型转换、default=默认值、action="store_true" 开关
#   - 脚本规范：main(argv) 接收参数列表，方便测试（第212课）

import argparse


def build_parser():
    parser = argparse.ArgumentParser(description="问候工具")
    parser.add_argument("name", help="要问候的人")
    parser.add_argument("-n", "--times", type=int, default=1, help="重复次数")
    parser.add_argument("--loud", action="store_true", help="大写输出")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)     # argv=None 时自动读真实命令行
    for _ in range(args.times):
        msg = f"你好，{args.name}！"
        print(msg.upper() if args.loud else msg)
    return 0


if __name__ == "__main__":
    # 演示：直接运行时用“内置模拟参数”跑一遍，方便观察效果
    # 真实使用：python 本文件.py 小明 -n 3 --loud
    print("== 演示1：小明 -n 2 --loud ==")
    main(["小明", "-n", "2", "--loud"])
    print("== 演示2：小红 ==")
    main(["小红"])
    print("提示：把本文件复制为 greet.py，终端运行 greet.py --help 可看到自动帮助")

# ===== 练习题 =====
# 1. 给工具加 --greeting 参数自定义问候语，默认“你好”。
# 2. 加参数校验：--times 小于 1 时用 parser.error() 报错退出。
# 3. 在终端运行 python 本文件.py --help，阅读自动生成的帮助。
# 4. 思考：main(argv) 写法为什么比直接读 sys.argv 更好测试？
