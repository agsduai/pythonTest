# ===== 第382课：文本处理与搜索-文本预处理 =====
# 知识点：
#   - 文本挖掘第一步：清洗 → 分词 → 去停用词 → 归一化
#   - 英文：小写化、去标点、按空白切分、过滤停用词
#   - 中文没有空格：可用“最大正向匹配”（词典法），未登录词按单字处理
#   - 停用词：the/a/is、的/了/吗 —— 高频但无信息量的词
#   - 预处理质量直接决定后续搜索/分类的天花板

import re

# ---- 停用词表（演示用，真实项目有几百个）----
STOPWORDS_EN = set("the a an is are was were to of and in on for with it this that".split())
STOPWORDS_ZH = set("的 了 吗 呢 吧 啊 是 在 和 与".split())


def clean_text(text: str) -> str:
    """小写化 + 去标点 + 压缩空白。"""
    text = text.lower()
    text = re.sub(r"[^\w\u4e00-\u9fa5]+", " ", text)   # 保留字母/数字/下划线/汉字
    return re.sub(r"\s+", " ", text).strip()


def tokenize_en(text: str) -> list[str]:
    """英文分词：清洗 → 空白切分 → 去停用词。"""
    return [w for w in clean_text(text).split() if w and w not in STOPWORDS_EN]


# ---- 中文最大正向匹配：词典有多长，就优先匹配多长 ----
DICT_ZH = ["今天", "天气", "真好", "我们", "公园", "散步", "喜欢", "编程", "北京", "哪里"]
MAX_LEN = max(len(w) for w in DICT_ZH)


def cut_zh(text: str) -> list[str]:
    """最大正向匹配分词；词典里没有的字，按单字输出。"""
    tokens, i = [], 0
    while i < len(text):
        matched = None
        for size in range(min(MAX_LEN, len(text) - i), 0, -1):
            candidate = text[i:i + size]
            if candidate in DICT_ZH:
                matched = candidate
                break
        if matched:
            tokens.append(matched)
            i += len(matched)
        else:
            tokens.append(text[i])          # 未登录词：单字兜底
            i += 1
    return [t for t in tokens if t not in STOPWORDS_ZH and t.strip()]


# ---- 演示 ----
en = "The Quick brown fox, is jumping over   the lazy dog!"
print("英文原文：", en)
print("清洗后：", clean_text(en))
print("分词结果：", tokenize_en(en))

zh = "今天天气真好，我们去公园散步，你喜欢编程吗？"
print("\n中文原文：", zh)
print("最大匹配：", cut_zh(zh))
print("（对比按字切分：", list(zh), "）")

# 词频统计（预处理 → 统计，一条最小流水线）
from collections import Counter

tokens = tokenize_en(en)
freq = Counter(tokens)
print("\n英文词频：", freq.most_common(5))

# ===== 练习题 =====
# 1. 给中文词典补充“数据”“分析”“学习”，再跑一次最大匹配。
# 2. 实现“最大逆向匹配”（从右往左匹配），对比两种结果。
# 3. 把 clean_text 改成“保留数字”（如价格 199.9），需要改哪一处正则？
# 4. 思考：词典法分词遇到新词（如“扫地机器人”）会怎样？
