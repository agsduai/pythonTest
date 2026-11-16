# ===== 第851课：生物信息学与序列算法-FASTA解析与GC含量 =====
# 知识点：
#   - FASTA 是生物序列的标准文本格式：>头信息 换行 ATCG 序列（可多行）
#   - 解析器要处理：多记录、多行拼接、空行、非法字符校验
#   - GC 含量 = (G+C)/(A+T+G+C)：不同物种、不同区域 GC 含量差异显著
#   - 互补配对 A-T、C-G；反向互补 = 反转 + 互补；DNA→RNA 是 T→U
#   - 本章后续课程全部建立在本课的解析与统计之上
# 依赖：无（标准库）

VALID = set("ACGTN")


def parse_fasta(text):
    """解析 FASTA 文本 -> [(header, seq)]。"""
    records = []
    header, chunks = None, []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                records.append((header, "".join(chunks)))
            header, chunks = line[1:].strip(), []
        else:
            if header is None:
                raise ValueError("FASTA 数据必须以 > 开头")
            chunks.append(line.upper())
    if header is not None:
        records.append((header, "".join(chunks)))
    return records


def validate(seq):
    bad = set(seq) - VALID
    if bad:
        raise ValueError(f"非法碱基: {sorted(bad)}")


def base_counts(seq):
    return {b: seq.count(b) for b in "ACGT"}


def gc_content(seq):
    n = sum(base_counts(seq).values())
    if n == 0:
        return 0.0
    return (seq.count("G") + seq.count("C")) / n


def reverse_complement(seq):
    table = {"A": "T", "T": "A", "C": "G", "G": "C", "N": "N"}
    return "".join(table[b] for b in reversed(seq))


def transcribe(seq):
    """DNA -> RNA：T 替换为 U。"""
    return seq.replace("T", "U")


def to_fasta(header, seq, width=60):
    lines = [">" + header]
    for i in range(0, len(seq), width):
        lines.append(seq[i:i + width])
    return "\n".join(lines)


print("== 解析多记录 FASTA ==")
sample = """>sp|HUMAN|Example1 Homo sapiens fragment
ATGGCCTATTGGAACGT
GCAAGCTTTGACCATG
>sp|MOUSE|Example2 高GC区段
GCGCGCGCGCGCGCGCGCGCGCGCGCGC
>sp|YEAST|Example3 低GC区段
ATATATATATATATATATATATATATATATAT
"""
records = parse_fasta(sample)
for header, seq in records:
    validate(seq)
print(f"  记录数 = {len(records)}")
for header, seq in records:
    print(f"  [{header.split()[0]}] 长度={len(seq):>3}  序列={seq[:16]}...")

print("\n== 碱基组成与 GC 含量 ==")
print(f"  {'ID':<22}{'长度':>5}{'A':>4}{'C':>4}{'G':>4}{'T':>4}{'GC%':>8}")
for header, seq in records:
    c = base_counts(seq)
    print(f"  {header.split()[0]:<22}{len(seq):>5}{c['A']:>4}{c['C']:>4}{c['G']:>4}{c['T']:>4}"
          f"{gc_content(seq):>8.1%}")

print("\n== 反向互补与回文位点 ==")
ecori = "GAATTC"
rc = reverse_complement(ecori)
print(f"  EcoRI 位点 {ecori} 的反向互补 = {rc}（回文：限制酶沿两链同位点切割）")
seq1 = records[0][1]
print(f"  序列1:      {seq1[:20]}")
print(f"  反向互补:   {reverse_complement(seq1)[:20]}")
print(f"  转录为 mRNA: {transcribe(seq1[:20])}")

print("\n== 序列写出再读入（往返一致）==")
out_text = "\n".join(to_fasta(h.split()[0], s) for h, s in records)
roundtrip = parse_fasta(out_text)
same = all(a[0] == b[0].split()[0] and a[1] == b[1]
           for a, b in zip(records, roundtrip))
print(f"  写出 {len(out_text.splitlines())} 行 -> 重新解析 {len(roundtrip)} 条 -> 一致: {same}")

print("\n== 错误处理 ==")
for label, text, seq in (
    ("缺 > 头", "ATGC", None),
    ("非法字符", ">x\nATGCXZ", None),
    ("空序列", ">\n", None),
):
    try:
        if label == "非法字符":
            validate("ATGCXZ")
        elif label == "缺 > 头":
            parse_fasta(text)
        else:
            rs = parse_fasta(text)
            validate(rs[0][1])
        print(f"  {label}: 未报错（不应该）")
    except Exception as exc:
        print(f"  {label}: {type(exc).__name__}: {exc}")

print("\n== 小结 ==")
for line in (
    "  解析器 = 逐行状态机：遇到 > 开新记录，否则拼接到当前记录",
    "  GC 含量是最基础的序列统计：物种鉴定、基因预测的第一线索",
    "  反向互补是双链生物学的核心操作，后续 ORF 搜索要用到负链",
    "  错误要在解析层尽早暴露，而不是让下游默默算出错误结果",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 FASTQ 解析：4 行一组（头、序列、+、质量行，Phred+33），过滤出低质量
#    （Q<20）碱基比例超过 10% 的记录。
# 2. 实现滑动窗口 GC 含量：窗口 40、步长 10，输出每窗口 GC% 并找出 GC 峰值区域。
# 3. 按 GC 含量从高到低重排 FASTA 记录并写出新的 FASTA 文本。
# 4. 思考：FASTA 头信息常用 "|" 分隔多字段（如 sp|P12345|NAME），解析时直接按
#    "|" 拆分有什么风险？
