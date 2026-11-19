# ===== 第992课：数据验证与转换-批量数据验证与异常处理 =====
# 知识点：
#   - try/except 捕获转换错误，不让一条坏数据毁掉整批
#   - 收集错误而不是遇到就停—— 一次给用户全部反馈
#   - 错误信息要包含位置和原因，方便定位
#   - 好数据继续处理，坏数据记录下来单独处理
# 依赖：无（标准库）

# 模拟一批待验证的数据
raw_scores = [
    {"name": "张三", "score": "85"},
    {"name": "李四", "score": "92"},
    {"name": "王五", "score": "abc"},       # 非数字
    {"name": "赵六", "score": "-5"},        # 超出范围
    {"name": "钱七", "score": ""},           # 空值
    {"name": "孙八", "score": "78"},
    {"name": "", "score": "90"},            # 缺少姓名
]

print("== 逐条验证 ==")
valid_scores = []
invalid_scores = []

for i, record in enumerate(raw_scores):
    name = record["name"].strip()
    score_text = record["score"].strip()

    # 验证姓名
    if not name:
        invalid_scores.append({"row": i + 1, "name": name,
                               "error": "姓名为空"})
        continue

    # 验证分数
    if not score_text:
        invalid_scores.append({"row": i + 1, "name": name,
                               "error": "分数为空"})
        continue
    if not score_text.replace("-", "").isdigit():
        invalid_scores.append({"row": i + 1, "name": name, "score": score_text,
                               "error": "分数不是纯数字"})
        continue

    score = int(score_text)
    if score < 0 or score > 100:
        invalid_scores.append({"row": i + 1, "name": name, "score": score,
                               "error": f"分数 {score} 超出范围 0-100"})
        continue

    valid_scores.append({"name": name, "score": score})

print(f"  有效: {len(valid_scores)} 条, 无效: {len(invalid_scores)} 条")

print("\n== 有效数据 ==")
for record in valid_scores:
    print(f"  {record['name']}: {record['score']}")

print("\n== 无效数据 ==")
for record in invalid_scores:
    detail = ", ".join(f"{k}={v}" for k, v in record.items() if k != "row")
    print(f"  第 {record['row']} 行: {detail}")

# 计算平均分（只算有效数据）
if valid_scores:
    avg = sum(s["score"] for s in valid_scores) / len(valid_scores)
    print(f"\n  有效数据平均分 = {avg:.1f}")

# 统计错误类型
from collections import Counter
error_types = Counter(r["error"].split("：")[0] if "：" in r["error"]
                      else r["error"] for r in invalid_scores)
print(f"  错误类型分布: {dict(error_types)}")

# ===== 练习题 =====
# 1. 增加一条验证规则：姓名不能超过 5 个字符。
# 2. 实现「批量转换」：把 ["1", "2", "abc", "4"] 转为 [1, 2, "abc", 4]，
#    转换失败的保留原值。
# 3. 输出有效数据的最高分和最低分。
# 4. 思考：为什么「收集所有错误再一起报」比「遇到第一个就停」更好？
