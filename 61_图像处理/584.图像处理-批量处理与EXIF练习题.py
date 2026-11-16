# ===== 第584课：图像处理-批量处理与EXIF =====
# 知识点：
#   - EXIF：照片元数据（拍摄时间、相机、方向、GPS）
#   - ImageOps.exif_transpose：按 EXIF 方向自动旋转（手机照片必备）
#   - 批量流程：遍历目录 → 修正方向 → 缩放 → 转 RGB → 保存 → 记录清单
#   - 隐私：EXIF 可能含 GPS/设备信息，对外发布前应清除
#   - 清单（manifest）：原文件、输出文件、尺寸、体积、哈希，便于审计
#   - 与第237课文件整理器、第45章ETL的批量处理思路一致
# 依赖：pip install pillow

import csv
import hashlib
import os
import tempfile
from pathlib import Path

from PIL import Image, ImageOps

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    source = root / "source"
    output = root / "output"
    thumbs = root / "thumbs"
    source.mkdir()
    output.mkdir()
    thumbs.mkdir()

    # ---- 生成测试图片（带 EXIF 拍摄时间）----
    for i, size in enumerate(((800, 600), (1200, 900), (640, 480)), 1):
        img = Image.new("RGB", size, (40 * i, 80, 160))
        exif = Image.Exif()
        exif[306] = f"2026:11:{10 + i:02d} 10:00:00"     # DateTime
        exif[271] = "DemoCam"                              # Make
        path = source / f"photo_{i}.jpg"
        img.save(path, exif=exif, quality=90)
        print(f"  生成 {path.name}，尺寸 {size}，EXIF 时间 {exif[306]}")

    # ---- 读取 EXIF ----
    print("\n== 读取 EXIF ==")
    with Image.open(source / "photo_1.jpg") as im:
        exif = im.getexif()
        print("  DateTime(306)：", exif.get(306))
        print("  Make(271)：", exif.get(271))
        print("  条目数：", len(exif))

    # ---- 批量处理 ----
    manifest = []
    for path in sorted(source.glob("*.jpg")):
        with Image.open(path) as im:
            original_size = im.size
            # 1) 按 EXIF 方向修正
            im = ImageOps.exif_transpose(im)
            # 2) 限制最大宽度 600
            if im.width > 600:
                ratio = 600 / im.width
                im = im.resize((600, int(im.height * ratio)), Image.Resampling.LANCZOS)
            # 3) 转 RGB（JPEG 不支持 RGBA）
            if im.mode != "RGB":
                im = im.convert("RGB")
            # 4) 保存（不带 exif → 清除元数据）
            out_path = output / path.name
            im.save(out_path, quality=85)
            # 5) 缩略图
            thumb = im.copy()
            thumb.thumbnail((160, 160), Image.Resampling.LANCZOS)
            thumb.save(thumbs / path.name, quality=80)

        digest = hashlib.sha256(out_path.read_bytes()).hexdigest()[:16]
        manifest.append({
            "source": path.name,
            "original": f"{original_size[0]}x{original_size[1]}",
            "output": f"{im.width}x{im.height}",
            "bytes": out_path.stat().st_size,
            "sha256_16": digest,
        })

    print("\n== 批量处理结果 ==")
    for row in manifest:
        print(f"  {row['source']}: {row['original']} → {row['output']}，"
              f"{row['bytes']} 字节，sha={row['sha256_16']}")

    # ---- 写清单 CSV ----
    manifest_path = root / "manifest.csv"
    with open(manifest_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(manifest[0].keys()))
        writer.writeheader()
        writer.writerows(manifest)
    print(f"\n清单：{manifest_path.name}（{len(manifest)} 行）")

    # ---- 验证输出 EXIF 已清除 ----
    with Image.open(output / "photo_1.jpg") as im:
        print("输出文件 EXIF 条目：", len(im.getexif()))
    print("  （重新保存时未传 exif → 元数据被清除）")

    # ---- 目录清单 ----
    print("\n== 输出目录 ==")
    for folder in (output, thumbs):
        print(f"  {folder.name}/：{sorted(p.name for p in folder.iterdir())}")

# ---- EXIF 与隐私 ----
print("\n== EXIF 隐私 ==")
for item in [
    "GPS 坐标会暴露拍摄地点",
    "设备型号/序列号可能识别个人",
    "拍摄时间可推断作息",
    "社交平台通常会自动清除，但自建服务要注意",
    "对外发布前统一 exif_transpose 后重新保存（不带 exif）",
]:
    print("  -", item)

# ---- 批量处理注意 ----
print("\n== 批量处理注意 ==")
for item in [
    "先备份原图，输出到新目录（本课 source/output 分离）",
    "处理失败的单个文件要记录并跳过，不要中断整批",
    "统一命名规则，避免重名覆盖",
    "大图逐张处理，不要一次性全部读入内存",
    "清单记录哈希，便于校验与去重",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给批量处理增加“只处理宽度 > 800 的图”。
# 2. 把输出格式改成 WebP，比较体积。
# 3. 统计 manifest 中所有输出文件的总大小。
# 4. 思考：为什么手机照片需要先 exif_transpose 再缩放？
