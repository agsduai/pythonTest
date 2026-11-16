# ===== 第752课：编译原理与代码优化-循环优化与强度削弱 =====
# 知识点：
#   - 循环是热点：绝大多数执行时间花在少量循环里，优化收益最大
#   - 循环不变量外提 LICM：把循环内每次都不变的计算移到 preheader
#   - 强度削弱 strength reduction：把乘法/幂换成加法/移位（i*4 -> 累加 +4）
#   - 归纳变量归纳：i 与 j=i*4 同步增长，可只保留一个并消去另一个
#   - 循环展开 unroll：减少分支与循环控制开销，代价是代码体积
#   - 循环融合/分裂/交换：改善局部性与并行性（本课只做前四种）
#   - 本课对小型 IR 逐项变换，并用解释执行验证语义等价
# 依赖：无（标准库）
OPS = {"+": lambda a,b:a+b, "-": lambda a,b:a-b, "*": lambda a,b:a*b}


def run(ir, env0):
    env = dict(env0)
    for dst, op, x, y in ir:
        xv = env.get(x, x) if isinstance(x, str) else x
        yv = env.get(y, y) if isinstance(y, str) else y
        if op == "const": env[dst] = xv
        elif op == "copy": env[dst] = xv
        else: env[dst] = OPS[op](xv, yv)
    return env


# 原始循环：for i in 0..n: s += i*4 + base
ORIGINAL = [
    ("base", "const", 100, None),
    ("n", "const", 5, None),
    ("i", "const", 0, None),
    ("s", "const", 0, None),
    ("c", "*", "i", 4),          # 循环体：i*4 每次算乘法
    ("t", "+", "c", "base"),     # base 是循环不变量
    ("s", "+", "s", "t"),
    ("i", "+", "i", 1),
    ("cond", "-", "i", "n"),
]
# 说明：这里把循环体展开 5 次来做等价验证（真实编译器用回边）
def unroll(loop_body, times, init):
    code = list(init)
    for _ in range(times):
        code.extend(loop_body)
    return code

INIT = ORIGINAL[:4]
BODY = ORIGINAL[4:8]
FULL = unroll(BODY, 5, INIT)
print("== 原始循环（展开 5 次以便对比）==")
for ins in FULL[:12]:
    print("   ", ins)
print(f"  ... 共 {len(FULL)} 条指令")
res0 = run(FULL, {})
print(f"  结果: s={res0['s']}, i={res0['i']}")

print("\n== 优化 1：循环不变量外提（LICM）==")
# base 在循环内不变，把 t = c + base 里的 base 提前算好（这里演示把不变计算提到外面）
LICM_INIT = INIT + [("base2", "copy", "base", None)]
LICM_BODY = [("c", "*", "i", 4), ("t", "+", "c", "base2"),
             ("s", "+", "s", "t"), ("i", "+", "i", 1)]
licm = unroll(LICM_BODY, 5, LICM_INIT)
print("  preheader 增加：base2 = base（循环内只引用已算好的量）")
print(f"  结果一致: s={run(licm,{})['s']} == {res0['s']}")

print("\n== 优化 2：强度削弱（i*4 -> 累加 +4）==")
# 用归纳变量 j 代替 i*4：j 初始 0，每次 +4
SR_INIT = [("base", "const", 100, None), ("n", "const", 5, None),
           ("i", "const", 0, None), ("j", "const", 0, None), ("s", "const", 0, None)]
SR_BODY = [("t", "+", "j", "base"),
           ("s", "+", "s", "t"),
           ("j", "+", "j", 4),           # 乘法被加法取代
           ("i", "+", "i", 1)]
sr = unroll(SR_BODY, 5, SR_INIT)
print("  原: c = i * 4（乘法）; 优化后: j += 4（加法），j 始终等于 i*4")
r = run(sr, {})
print(f"  结果: s={r['s']}, j={r['j']}  与原一致={r['s'] == res0['s']}")

print("\n== 优化 3：归纳变量消除 ==")
# i 只用于控制循环次数，可完全删掉，用 j 判断终止
IVE_INIT = [("base", "const", 100, None), ("j", "const", 0, None),
            ("s", "const", 0, None), ("limit", "const", 20, None)]
IVE_BODY = [("t", "+", "j", "base"), ("s", "+", "s", "t"), ("j", "+", "j", 4)]
ive = unroll(IVE_BODY, 5, IVE_INIT)
r2 = run(ive, {})
print("  删掉 i，只用 j 与 limit=5*4 比较")
print(f"  结果: s={r2['s']}, 指令数 {len(FULL)} -> {len(ive)}，一致={r2['s']==res0['s']}")

print("\n== 优化 4：循环展开因子的影响 ==")
for u in (1, 2, 4, 5):
    # 展开 u 次意味着循环控制判断次数变成 5/u（示意）
    iters = (5 + u - 1) // u
    print(f"  unroll={u}: 循环体执行 {5} 次，控制分支从 5 次降为约 {iters} 次，"
          f"代码体积 ×{u}")

print("\n== 变换前后指令类型统计 ==")
from collections import Counter
for name, code in (("原始", FULL), ("强度削弱", sr), ("归纳变量消除", ive)):
    c = Counter(op for _, op, _, _ in code)
    print(f"  {name:<14}: 乘法={c['*']:>2} 加法={c['+']:>2} 指令总数={len(code)}")
print("  乘法从 5 次降到 0 次（老 CPU 上乘法远慢于加法）")

print("\n== 优化的正确性约束 ==")
for line in (
    "  LICM 只能外提「循环内没有写入」且「不会抛异常」的表达式",
    "  强度削弱要保持归纳变量之间的线性关系，溢出语义也要一致",
    "  浮点重结合会改变结果，很多优化需要 -ffast-math 才允许",
    "  每个优化 pass 都要有等价性验证（解释执行 / 形式化 / 测试）",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  先识别自然循环（第749课）才能安全做 LICM",
    "  现代 CPU 乘法已很快，强度削弱收益更多来自减少依赖链",
    "  循环展开要权衡 I-cache 压力，过度展开反而变慢",
    "  自动向量化是循环优化的更高形式（SIMD）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现真正的 LICM：用「循环内 def 集合」自动判定哪些指令可外提。
# 2. 给强度削弱加溢出检查语义，验证与原始乘法在边界值一致。
# 3. 实现循环融合：把两个遍历同一区间的循环合并成一个。
# 4. 思考：为什么浮点循环里不能随便做「重结合」优化？
