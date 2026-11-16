# ===== 第791课：形式语言与自动机-图灵机与可计算性 =====
# 知识点：
#   - 图灵机 = 有限状态控制 + 无限纸带 + 读写头；每步 读/写/移头/转状态
#   - 与 DFA 的区别：纸带可以「写回」，头可以左右移动，所以能当通用计算器
#   - 丘奇-图灵论题：一切「可机械计算」的问题都能被图灵机计算
#   - 停机问题不可判定：不存在程序能判定任意程序是否停机（对角线反证）
#   - 可计算性层次：可判定(decidable) ⊂ 半可判定(RE) ⊂ 不可判定
#   - 本课模拟图灵机跑二进制加 1、回文检查，并用对角化演示停机问题
# 依赖：无（标准库）


class TuringMachine:
    def __init__(self, transitions, start="start", halt="halt", blank="_"):
        self.delta = transitions       # (state, read) -> (write, move, next)
        self.start, self.halt, self.blank = start, halt, blank

    def run(self, tape, max_steps=2000):
        """tape 用字符串表示；返回 (最终纸带, 是否停机, 步数, 轨迹)。"""
        cells = {i: ch for i, ch in enumerate(tape)}
        head, state, steps = 0, self.start, 0
        trace = []
        lo = 0
        while steps < max_steps:
            if state == self.halt:
                break
            ch = cells.get(head, self.blank)
            key = (state, ch)
            if key not in self.delta:
                break
            write, move, nxt = self.delta[key]
            cells[head] = write
            trace.append((steps, state, ch, write, move, nxt))
            head += 1 if move == "R" else -1
            lo = min(lo, head)
            state = nxt
            steps += 1
        # 规范化纸带输出（去掉首尾空白）
        used = [i for i in range(lo, head + 1) if cells.get(i, self.blank) != self.blank]
        out = "".join(cells.get(i, self.blank) for i in range(min(used), max(used)+1)) if used else ""
        halted = state == self.halt
        return out, halted, steps, trace


print("== 图灵机 1：二进制数加 1 ==")
# 约定：从最右位开始，遇 1 变 0 并左移进位；遇 0 变 1 后回到最左核对
TM_INC = TuringMachine({
    ("start",  "1"): ("1", "L", "carry"),
    ("start",  "0"): ("1", "L", "done_back"),
    ("start",  "_"): ("1", "L", "done_back"),     # 空串/全 1 时补最高位
    ("carry",  "1"): ("0", "L", "carry"),
    ("carry",  "0"): ("1", "L", "done_back"),
    ("carry",  "_"): ("1", "L", "done_back"),
    ("done_back","_"): ("_", "R", "done"),
    ("done_back","0"): ("0", "R", "done_back"),
    ("done_back","1"): ("1", "R", "done_back"),
})
for n in ("1011", "111", "100", "0", "1111"):
    out, halt, steps, _ = TM_INC.run(n)
    got = int(out, 2) if out else 0
    print(f"  {n:>5}+1 -> {out:<6} 停机={halt} 步数={steps} "
          f"正确={got == int(n,2)+1}")

print("\n== 执行轨迹（1011 + 1）==")
_, _, _, trace = TM_INC.run("1011")
for step, state, read, write, move, nxt in trace:
    print(f"    step {step}: 状态={state:<10} 读={read} 写={write} 移动={move} -> {nxt}")

print("\n== 图灵机 2：回文检查（# 分隔 + 标记法）==")
# 思路：反复「读首字符→记下→扫到末尾比对→删除两端」，不等即拒绝
def is_palindrome_tape(s):
    """用图灵机思路（标记两端）模拟，教学用 Python 实现等价逻辑。"""
    tape = list(s + "#")
    left = 0
    right = len(tape) - 2
    marked = "X"
    while True:
        # 跳过左侧已标记
        while left < len(tape) and tape[left] == marked:
            left += 1
        # 找到有效左字符
        if left >= right:
            return True, tape
        ch = tape[left]
        tape[left] = marked
        # 从右向左找最后一个未标记且等于 ch 的位置
        r = right
        while r > left and tape[r] == marked:
            r -= 1
        if r == left:
            # 只剩自己（奇数长度中心）
            return True, tape
        if tape[r] != ch:
            tape[right] = "!"
            return False, tape
        tape[r] = marked
        right = r - 1
        # 跳过右侧已标记
        while right > left and tape[right] == marked:
            right -= 1
        if right <= left:
            return True, tape

for s in ("abba", "abcba", "abca", "ab", "a"):
    ok, tape = is_palindrome_tape(s)
    print(f"  {s!r:<8} -> 回文={ok}  标记后={''.join(tape)}")

print("\n== 停机问题的对角化反证 ==")
print("  假设 halts(p) 能判定任意程序 p 是否停机：")
print("    构造 trouble: if halts(trouble): 死循环 else: 停机")
print("    - 若 halts(trouble)=True（预测会停）→ trouble 死循环 → 预测错")
print("    - 若 halts(trouble)=False（预测不停）→ trouble 立即停 → 预测错")
print("  两种情况都矛盾 → halts 不可能存在（图灵 1936）")

print("\n== 可计算性层次 ==")
for line in (
    "  可判定 decidable: 总能在有限步给出 是/否（如 DFA 判空、语法分析）",
    "  半可判定 RE: 答案「是」时会停，「否」可能死循环（如程序存在某输入使其输出 1）",
    "  不可判定: 停机问题、Hilbert 第十问题（丢番图方程）、WCET 精确分析",
    "  与实践的关系：静态分析工具都只能给「近似」答案（第750课数据流分析）",
):
    print(" ", line)

print("\n== 图灵完备性 ==")
for line in [
    "  Python/JS/C 都是图灵完备的：有条件分支 + 可变存储即可模拟图灵机",
    "  正则表达式不是图灵完备（有限状态）；JSON 也不是（无计算）",
    "  判断「一个 DSL 是否图灵完备」很重要——配置语言不该图灵完备",
    "  与第74/82章解释器/编译器呼应：你写的解释器只要能模拟图灵机就是图灵完备的",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 写一台图灵机实现「二进制加法」（两个数用 # 分隔）。
# 2. 实现通用图灵机模拟器：输入「编码后的机器描述 + 输入带」。
# 3. 用对角化证明「没有程序能判定任意程序输出是否为 42」。
# 4. 思考：为什么停机问题不可判定，但静态分析工具仍然有用？
