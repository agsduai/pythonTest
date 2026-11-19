# ===== 第1060课：异常处理进阶-tryexceptelsefinally =====
# 知识点：
#   - else：try 里没出错时才执行，放"成功后要做的事"
#   - finally：无论成败都执行，放"必须收尾的事"（关文件、解锁）
#   - 完整结构：try -> except（出错时）-> else（成功时）-> finally（总是）
#   - 实际场景：读文件（成功才解析、无论如何都关闭）

# 案例一：完整四段结构演示
def safe_divide(a, b):
    print(f"尝试计算 {a} / {b}")
    try:
        result = a / b          # 可能出错的代码
    except ZeroDivisionError:
        print("  except：除数是 0，计算失败")
        return None
    else:
        print(f"  else：计算成功，结果 {result}")  # 只有成功才走
        return result
    finally:
        print("  finally：本轮计算收尾（总会执行）")  # 总会走

safe_divide(10, 2)
print("---")
safe_divide(10, 0)

# 案例二：else 的价值 —— 把"成功逻辑"和"风险逻辑"分开
# 场景：解析用户输入，成功才入库
def parse_amount(raw):
    try:
        value = float(raw)
    except ValueError:
        print(f"'{raw}' 不是数字，拒绝入库")
        return False
    else:
        print(f"金额 {value} 校验通过，已入库")
        return True

parse_amount("9.9")
parse_amount("abc")

# 案例三：finally 兜底 —— 无论如何都要清理
# 场景：模拟"打开文件处理，最后一定关闭"
class FakeFile:
    def close(self):
        print("  文件已关闭")

def process(path_exists):
    f = FakeFile() if path_exists else None
    try:
        if f is None:
            raise FileNotFoundError("文件不存在")
        print("  正在处理文件内容")
    except FileNotFoundError as e:
        print(f"  出错：{e}")
    finally:
        if f is not None:
            f.close()  # 不写 finally，出错时文件就没人关了

process(True)
process(False)

# 案例四：finally 中返回值会覆盖（了解坑）
# finally 里不要写 return，会吞掉 try/except 的返回值
def tricky():
    try:
        return "try 的返回值"
    finally:
        pass  # 若这里写 return "finally 的返回值"，try 的就被覆盖了

print(f"返回：{tricky()}")

# ===== 练习题 =====
# 1. 写完整 try/except/else/finally 结构的函数 read_config(dict)：键存在打印值（else），不存在捕获 KeyError，finally 打印"读取结束"。
# 2. 写函数 parse_int_safe(text)：ValueError 时返回 0 并提示，成功时用 else 打印"解析成功"，两种输入各测一次。
# 3. 模拟数据库操作：try 里 raise RuntimeError("连接中断")，except 打印回滚，finally 打印"释放连接"，验证 finally 在出错路径也执行。
