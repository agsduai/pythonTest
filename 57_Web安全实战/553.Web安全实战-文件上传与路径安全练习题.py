# ===== 第553课：Web安全实战-文件上传与路径安全 =====
# 知识点：
#   - 上传是高风险入口：可传 WebShell、超大文件、路径穿越、内容伪造
#   - 文件名不可信：只取 basename，过滤特殊字符，限制长度
#   - 扩展名白名单 + MIME/魔数校验（不能只看 Content-Type）
#   - 保存路径必须 resolve 后校验在根目录内，防 ../ 穿越
#   - 大小限制要在读取过程中检查，不能只信 Content-Length
#   - 上传目录不应有执行权限；图片最好重新编码（去元数据/去恶意载荷）
#   - 与第409课静态文件安全、第456课隔离坏数据呼应
# 依赖：无（pathlib/tempfile）

import re
import tempfile
from pathlib import Path

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".pdf"}
MAX_SIZE = 2 * 1024 * 1024          # 2MB

MAGIC = {
    b"\x89PNG\r\n\x1a\n": ".png",
    b"\xff\xd8\xff": ".jpg",
    b"GIF87a": ".gif",
    b"GIF89a": ".gif",
    b"%PDF-": ".pdf",
}


def sanitize_filename(name: str) -> str:
    """只取文件名部分，替换危险字符，限制长度。"""
    name = Path(name).name                      # 去掉 ../ 和目录
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    name = name.strip("._") or "upload"
    return name[:80]


def detect_type(head: bytes) -> str | None:
    for magic, ext in MAGIC.items():
        if head.startswith(magic):
            return ext
    return None


def safe_save(upload_dir: Path, filename: str, content: bytes) -> Path:
    upload_dir = upload_dir.resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)

    if len(content) > MAX_SIZE:
        raise ValueError(f"文件过大：{len(content)} 字节")
    if not content:
        raise ValueError("空文件")

    name = sanitize_filename(filename)
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"不允许的扩展名：{ext or '无'}")

    real_ext = detect_type(content[:16])
    if real_ext is None:
        raise ValueError("无法识别的文件类型（魔数校验失败）")
    if real_ext != ext and not (real_ext == ".jpg" and ext in (".jpg", ".jpeg")):
        raise ValueError(f"扩展名与内容不符：声明 {ext}，实际 {real_ext}")

    target = (upload_dir / name).resolve()
    if not target.is_relative_to(upload_dir):    # 双保险：路径必须在根内
        raise ValueError("非法路径")
    if target.exists():
        stem, suffix = target.stem, target.suffix
        i = 1
        while target.exists():
            target = upload_dir / f"{stem}_{i}{suffix}"
            i += 1

    target.write_bytes(content)
    return target


with tempfile.TemporaryDirectory() as tmp:
    upload_dir = Path(tmp) / "uploads"

    print("== 文件名清洗 ==")
    for name in ("../../etc/passwd", "a.php", "正常图片.png", "..\\..\\win.ini", "x" * 200 + ".png"):
        print(f"  {name[:30]!r:35s} → {sanitize_filename(name)!r}")

    # 准备一个合法 PNG（最小文件头即可通过魔数校验）
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    print("\n== 合法上传 ==")
    saved = safe_save(upload_dir, "photo.png", png)
    print("  保存到：", saved.name, "| 大小", saved.stat().st_size)

    # 重名自动改名
    saved2 = safe_save(upload_dir, "photo.png", png)
    print("  重名保存：", saved2.name)

    print("\n== 攻击尝试 ==")
    attacks = [
        ("../../shell.php", png, "路径穿越+非法扩展"),
        ("shell.php", png, "非法扩展名"),
        ("fake.png", b"MZ\x90\x00" + b"\x00" * 100, "伪装成 PNG 的 EXE"),
        ("big.png", png + b"\x00" * (MAX_SIZE + 1), "超过大小限制"),
        ("empty.png", b"", "空文件"),
    ]
    for name, content, desc in attacks:
        try:
            safe_save(upload_dir, name, content)
            print(f"  ✗ {desc}：竟然通过")
        except ValueError as exc:
            print(f"  ✓ {desc}：{exc}")

    print("\n== 目录内容 ==")
    for p in sorted(upload_dir.iterdir()):
        print("  ", p.name, p.stat().st_size, "字节")

# ---- 存储与环境安全 ----
print("\n== 存储与环境 ==")
for item in [
    "上传目录放在 Web 根目录之外，或禁止执行脚本",
    "文件名用随机 UUID，不用用户原始名",
    "图片重新编码（Pillow）可去掉 EXIF 与嵌入载荷",
    "对象存储用私有桶 + 临时签名 URL",
    "上传记录审计：谁、何时、原文件名、大小、哈希",
]:
    print("  -", item)

# ---- 检查清单 ----
print("\n== 上传检查清单 ==")
for item in [
    "扩展名白名单（不是黑名单）",
    "魔数/MIME 校验",
    "大小限制（流式读取时检查）",
    "文件名清洗 + 路径 resolve 校验",
    "重名处理不覆盖",
    "存储与执行分离",
    "病毒扫描/内容审核（高风险业务）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 增加 .webp 支持，并写对应魔数。
# 2. 实现“流式保存”：边读边计数，超过上限立即中止。
# 3. 用 Pillow 重新编码图片，验证 EXIF 被清除。
# 4. 思考：为什么“只检查 Content-Type”完全不可靠？
