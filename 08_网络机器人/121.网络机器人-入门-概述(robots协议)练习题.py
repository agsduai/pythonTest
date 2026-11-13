# ===== 第121课：网络机器人-入门-概述(robots协议) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - robots.txt 是站点放在根目录、写给爬虫看的访问约定
#   - User-agent 指定适用的爬虫，Disallow/Allow 指定禁止/允许的路径
#   - Crawl-delay 建议访问间隔；Sitemap 给出站点地图位置
#   - Python 标准库 urllib.robotparser 可解析 robots 并判断 can_fetch
# 依赖：无（仅使用 Python 标准库 urllib）

from urllib.robotparser import RobotFileParser

ROBOTS_TEXT = """\
User-agent: *
Disallow: /private/
Allow: /public/
Crawl-delay: 2

User-agent: StudyBot
Disallow: /tmp/
"""


def load_from_text(text: str) -> RobotFileParser:
    """解析内存中的 robots 文本，便于离线学习。"""
    parser = RobotFileParser()
    parser.parse(text.splitlines())
    return parser


def load_from_web(robots_url: str) -> RobotFileParser:
    """联网读取 robots.txt；网络失败时由调用方处理异常。"""
    parser = RobotFileParser()
    parser.set_url(robots_url)
    parser.read()
    return parser


def check(parser: RobotFileParser, url: str, agent: str = "StudyBot") -> tuple:
    """返回（是否允许访问，建议的抓取间隔秒数）。"""
    return parser.can_fetch(agent, url), parser.crawl_delay(agent)


if __name__ == "__main__":
    parser = load_from_text(ROBOTS_TEXT)
    # OtherBot 命中通配组；StudyBot 命中专用组，专用组会覆盖通配组
    print("OtherBot 访问 /public/list：", check(parser, "https://example.com/public/list", "OtherBot"))
    print("OtherBot 访问 /private/data：", check(parser, "https://example.com/private/data", "OtherBot"))
    print("StudyBot 访问 /tmp/cache：", check(parser, "https://example.com/tmp/cache"))

# ===== 练习题 =====
# 1. 写出三条常见 robots 指令的含义：User-agent、Disallow、Crawl-delay。
# 2. 用 load_from_web 读取 https://quotes.toscrape.com/robots.txt 并测试首页是否可抓。
# 3. 若目标站点禁止抓取某目录，程序应如何调整？请给出两种替代方案。
