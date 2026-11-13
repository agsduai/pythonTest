# ===== 第092课：AI应用-大模型调用-网络基础知识 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 网络通信的基本模型：客户端（浏览器/程序）向服务器发请求，服务器返回响应
#   - IP 地址：网络中一台主机的地址；域名：便于记忆的别名，需要 DNS 解析
#   - 端口：同一台主机上不同服务的编号，HTTP 默认 80，HTTPS 默认 443
#   - localhost / 127.0.0.1 表示本机；Ollama 默认监听 11434 端口
#   - URL 组成：协议://主机:端口/路径?查询参数
#   - 跨网络访问要设置超时，网络失败是正常情况，程序必须能处理异常
# 依赖：无（仅使用标准库 socket 与 urllib.parse）

import socket
from urllib.parse import urlparse


def parse_url(url):
    """拆解 URL，并推断实际使用的端口。"""
    parsed = urlparse(url)
    default_port = 443 if parsed.scheme == "https" else 80
    port = parsed.port or default_port  # URL 没写端口时使用协议默认端口
    print(f"协议：{parsed.scheme}")
    print(f"主机：{parsed.hostname}")
    print(f"端口：{port}")
    print(f"路径：{parsed.path}")
    print(f"查询参数：{parsed.query}")
    return parsed.hostname, port


def check_port(host, port, timeout=3):
    """自检脚本：尝试建立 TCP 连接，判断目标服务是否可达。"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            print(f"[成功] {host}:{port} 可以连接")
            return True
    except socket.gaierror:
        print(f"[失败] 域名无法解析：{host}")
    except TimeoutError:
        print(f"[超时] {host}:{port} 在 {timeout} 秒内没有响应")
    except OSError as exc:
        print(f"[失败] {host}:{port} 连接失败：{exc}")
    return False


if __name__ == "__main__":
    print("== 解析 API 地址 ==")
    host, port = parse_url("https://api.deepseek.com/chat/completions")
    print("\n== 检查网络连通性 ==")
    check_port(host, port)                 # 云端 API，需要联网
    check_port("localhost", 11434)         # 本地 Ollama 服务，需先启动

# ===== 练习题 =====
# 1. 用 urlparse 解析 "http://localhost:11434/api/chat?stream=false"，打印各组成部分。
# 2. 启动 Ollama 后运行 check_port("localhost", 11434)，再用未启动的服务端口对比结果。
# 3. 自测：HTTPS 默认使用哪个端口？为什么程序中访问网络要设置 timeout？
