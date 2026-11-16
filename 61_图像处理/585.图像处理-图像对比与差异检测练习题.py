# ===== 第585课：图像处理-图像对比与差异检测 =====
# 知识点：
#   - ImageChops.difference(a,b)：逐像素求差，相同处为黑
#   - getbbox()：非零区域的外接矩形，快速定位变化位置
#   - ImageStat.Stat：均值、RMS，衡量整体差异
#   - 相似度：1 - 变化像素数 / 总像素数
#   - 阈值：微小压缩噪声不应算“变化”，先 point 过滤
#   - 应用：UI 回归测试（截图对比）、监控画面变化、找不同
#   - 与第20章哈希校验的区别：哈希只能判断“变没变”，图像对比能定位“哪里变”
# 依赖：pip install pillow numpy

import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageStat

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)

    # ---- 构造两张图：第二张改一个矩形 ----
    base = Image.new("RGB", (400, 300), "#F0F0F0")
    draw = ImageDraw.Draw(base)
    draw.rectangle([40, 40, 160, 120], fill="#4C78A8")
    draw.text((50, 160), "V1", fill="black")
    base.save(tmp / "v1.png")

    changed = base.copy()
    cd = ImageDraw.Draw(changed)
    cd.rectangle([200, 100, 340, 220], fill="#E45756")   # 新增块
    cd.text((50, 160), "V2", fill="black")                # 文字变化
    changed.save(tmp / "v2.png")

    # ---- 逐像素差异 ----
    diff = ImageChops.difference(base, changed)
    diff.save(tmp / "diff.png")
    bbox = diff.getbbox()
    print("== 差异区域 ==")
    print("  外接矩形：", bbox, "（左,上,右,下）")
    print("  差异图已保存 diff.png（相同处为黑）")

    # ---- 统计差异 ----
    arr = np.array(diff)
    changed_pixels = int(np.any(arr > 0, axis=2).sum())
    total_pixels = base.width * base.height
    print("\n== 统计 ==")
    print(f"  变化像素：{changed_pixels} / {total_pixels} "
          f"（{changed_pixels / total_pixels:.1%}）")
    print(f"  相似度：{1 - changed_pixels / total_pixels:.2%}")
    stat = ImageStat.Stat(diff)
    print("  各通道 RMS：", [round(v, 2) for v in stat.rms])
    print("  平均差异：", [round(v, 2) for v in stat.mean])

    # ---- 阈值过滤：忽略微小噪声 ----
    gray_diff = diff.convert("L")
    for threshold in (0, 10, 30):
        mask = gray_diff.point(lambda v: 255 if v > threshold else 0)
        bbox_t = mask.getbbox()
        count = int((np.array(mask) > 0).sum())
        print(f"\n  阈值 {threshold:2d}：变化像素 {count:5d}，区域 {bbox_t}")

    # ---- 定位具体变化 ----
    print("\n== 变化区域分组（简化：按外接矩形）==")
    print("  新增红色块位于 (200,100)~(340,220)")
    print("  文字从 V1 变成 V2，位于 (50,160) 附近")

    # ---- 对比“完全相同” ----
    identical_diff = ImageChops.difference(base, base.copy())
    print("\n== 相同图片 ==")
    print("  bbox：", identical_diff.getbbox(), "（None 表示完全相同）")
    print("  变化像素：", int(np.any(np.array(identical_diff) > 0, axis=2).sum()))

# ---- 应用场景 ----
print("\n== 应用场景 ==")
for item in [
    "UI 回归测试：新版本截图与基线对比，发现意外改动",
    "视频监控：画面出现大块变化时告警",
    "文档扫描：检测两次扫描是否有修改",
    "找不同游戏：直接定位差异区域",
]:
    print("  -", item)

# ---- 注意 ----
print("\n== 注意 ==")
for item in [
    "抗锯齿/压缩噪声会造成小差异，先设阈值",
    "尺寸不同的图要先统一尺寸/对齐",
    "动态内容（时间、广告）会误报，需遮罩区域",
    "颜色空间不同（RGB vs RGBA）要先统一",
    "感知差异 ≠ 像素差异，人眼对亮度更敏感",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 计算两张图的“结构相似度”简化版（1 - RMS/255）。
# 2. 只对比某个区域（crop 后比较），忽略时钟区域。
# 3. 把差异区域用红框画在原图上保存。
# 4. 思考：为什么 UI 测试不能只比较哈希？
