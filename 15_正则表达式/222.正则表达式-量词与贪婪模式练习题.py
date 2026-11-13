# ===== 第222课：正则表达式-量词与贪婪模式 =====
# 知识点：
#   - 量词：* 零次以上；+ 一次以上；? 零或一次；{n} {n,} {n,m}
#   - 贪婪模式：量词默认“尽可能多”地匹配
#   - 非贪婪：量词后面再加一个 ?，变成“尽可能少”
#   - 经典坑：用 .* 解析 HTML 标签会“吃”过头

import re

# 量词基础
print(re.findall(r"\d{3}", "12345 678"))          # 精确 3 位
print(re.findall(r"\d{2,4}", "1 12 123 12345"))   # 2~4 位，能多吃就多吃
print(re.findall(r"go?d", "gd god good"))         # o 可有可无
print(re.findall(r"go+d", "gd god good gooood"))  # o 至少一个
print(re.findall(r"https?://\S+", "http://a.com https://b.com"))

# 贪婪 vs 非贪婪：HTML 标签经典案例
s = "<div>标题</div><div>正文</div>"
print(re.findall(r"<div>.*</div>", s))      # 贪婪：一口气吃到最后一个 </div>
print(re.findall(r"<div>.*?</div>", s))     # 非贪婪：碰到第一个 </div> 就停

# 贪婪在重复字符上的体现
print(re.findall(r"\d+", "8888"))     # ['8888']：尽量多吃
print(re.findall(r"\d+?", "8888"))    # ['8', '8', '8', '8']：尽量少吃

# ? 的两种身份：作为量词（0或1次）、作为非贪婪开关
print(re.findall(r"colou?r", "color colour"))
print(re.findall(r"\d{2,4}?", "12345"))   # 非贪婪：满足 2 位就停

# ===== 练习题 =====
# 1. 用量词改写第221课的“6位邮编”校验：^\d{6}$。
# 2. 从 "<p>第一段</p><p>第二段</p>" 中用非贪婪提取两个段落的文本。
# 3. 验证 {2,4} 与 {2,4}? 在 "123456" 上的输出差异并解释原因。
# 4. 思考：为什么解析 HTML 更推荐用 BeautifulSoup 而不是正则？
