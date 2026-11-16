# ===== 第586课：图像处理-综合案例-批量照片处理器 =====
# 知识点：
#   - 综合运用：打开/保存（579）+ 缩放（580）+ 滤镜增强（581）
#     + 水印（582）+ 批量/EXIF（584）+ 清单
#   - 流程：遍历 → EXIF 方向修正 → 限制尺寸 → 增强 → 水印
#     → 转 RGB → 保存 JPEG → 生成缩略图 → 记录清单
#   - 输出目录与源目录分离，失败文件记录不中断
#   - 水印用半透明叠加层，不破坏原图
#   - 交付：处理后的图片 + 缩略图 + manifest.csv + 汇总报告
# 依赖：pip install pillow

import csv
import hashlib
import os
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

MAX_WIDTH = 640
JPEG_QUALITY = 85
THUMB_SIZE = (160, 160)


def load_font(size: int):
    for path in ("C:/Windows/Fonts/arial.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                pass
    return ImageFont.load_default()


def make_sample_images(folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    specs = [
        ("photo_a.jpg", (1000, 700), (70, 130, 180)),
        ("photo_b.jpg", (800, 800), (220, 120, 60)),
        ("photo_c.jpg", (640, 420), (90, 180, 120)),
        ("photo_d.jpg", (1200, 900), (180, 90, 160)),
    ]
    for name, size, color in specs:
        img = Image.new("RGB", size, color)
        draw = ImageDraw.Draw(img)
        font = load_font(36)
        draw.text((30, 30), name, fill="white", font=font)
        draw.rectangle([30, 100, size[0] - 30, size[1] - 30],
                       outline="white", width=4)
        exif = Image.Exif()
        exif[306] = "2026:11:13 10:00:00"
        img.save(folder / name, exif=exif, quality=92)


def add_watermark(img: Image.Image, text: str = "SAMPLE") -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = load_font(max(18, img.width // 20))
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((img.width - w - 24, img.height - h - 20),
              text, font=font, fill=(255, 255, 255, 110))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def process_image(src: Path, out_dir: Path, thumb_dir: Path) -> dict:
    with Image.open(src) as im:
        original_size = im.size
        # 1) EXIF 方向
        im = ImageOps.exif_transpose(im)
        # 2) 限制宽度
        if im.width > MAX_WIDTH:
            ratio = MAX_WIDTH / im.width
            im = im.resize((MAX_WIDTH, int(im.height * ratio)), Image.Resampling.LANCZOS)
        # 3) 轻微增强
        im = ImageEnhance.Contrast(im).enhance(1.08)
        im = ImageEnhance.Sharpness(im).enhance(1.2)
        # 4) 水印
        im = add_watermark(im)
        # 5) 保存
        out_path = out_dir / src.name
        im.save(out_path, quality=JPEG_QUALITY, optimize=True)
        # 6) 缩略图
        thumb = im.copy()
        thumb.thumbnail(THUMB_SIZE, Image.Resampling.LANCZOS)
        thumb.save(thumb_dir / src.name, quality=80)

    digest = hashlib.sha256(out_path.read_bytes()).hexdigest()[:16]
    return {
        "file": src.name,
        "original": f"{original_size[0]}x{original_size[1]}",
        "output": f"{im.width}x{im.height}",
        "bytes": out_path.stat().st_size,
        "sha256_16": digest,
    }


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    source = root / "source"
    output = root / "output"
    thumbs = root / "thumbs"
    output.mkdir()
    thumbs.mkdir()

    make_sample_images(source)
    print("== 源文件 ==")
    for p in sorted(source.glob("*.jpg")):
        with Image.open(p) as im:
            print(f"  {p.name}: {im.size}，{p.stat().st_size} 字节")

    # ---- 批量处理（失败隔离）----
    print("\n== 批量处理 ==")
    manifest, failed = [], []
    for path in sorted(source.glob("*.jpg")):
        try:
            row = process_image(path, output, thumbs)
            manifest.append(row)
            print(f"  ✓ {row['file']}: {row['original']} → {row['output']}，"
                  f"{row['bytes']} 字节")
        except Exception as exc:
            failed.append((path.name, str(exc)))
            print(f"  ✗ {path.name}: {exc}")

    # ---- 清单 ----
    manifest_path = root / "manifest.csv"
    with open(manifest_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(manifest[0].keys()))
        writer.writeheader()
        writer.writerows(manifest)

    # ---- 汇总 ----
    total_bytes = sum(row["bytes"] for row in manifest)
    print("\n== 汇总 ==")
    print(f"  成功 {len(manifest)} 个，失败 {len(failed)} 个")
    print(f"  输出总大小：{total_bytes / 1024:.1f} KB")
    print(f"  平均大小：{total_bytes / len(manifest) / 1024:.1f} KB")
    print(f"  缩略图数量：{len(list(thumbs.glob('*.jpg')))}")
    print(f"  清单：{manifest_path.name}")

    # ---- 验证水印与尺寸 ----
    sample = output / "photo_a.jpg"
    with Image.open(sample) as im:
        print(f"\n  样例 {sample.name}：{im.size}，mode={im.mode}，"
              f"EXIF 条目={len(im.getexif())}")
        print("  （EXIF 已清除、宽度限制在 640、已转 RGB）")

# ---- 处理器清单 ----
print("\n== 处理器清单 ==")
for item in [
    "源目录只读，输出/缩略图/清单分离",
    "单文件失败不影响整批（try/except + failed 列表）",
    "EXIF 方向修正后再缩放，避免“横图变竖图”",
    "统一转 RGB，JPEG 不支持透明",
    "水印半透明，不遮挡主体",
    "清单记录原尺寸/输出尺寸/体积/哈希，便于审计",
]:
    print("  -", item)

# ---- 可扩展 ----
print("\n== 可扩展 ==")
for item in [
    "并行处理（第197课线程池）",
    "支持 WebP/AVIF 输出",
    "按拍摄日期分文件夹",
    "人脸/车牌自动模糊（隐私）",
    "上传对象存储并生成 CDN URL",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给处理器增加“最大高度”限制。
# 2. 用线程池并行处理（第197课），比较耗时。
# 3. 输出 WebP 并比较总体积。
# 4. 思考：为什么批量处理要先备份原图，且输出目录不能等于源目录？
