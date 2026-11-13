# ===== 第269课：加密安全-综合案例-文件完整性校验工具 =====
# 知识点：
#   - 综合运用：hashlib 摘要（第265课）+ hmac 验签（第267课）+ pathlib（第231课）
#   - 场景：为目录生成“指纹清单”，之后一键校验文件是否被篡改
#   - 清单本身也签名：防止攻击者连清单一起改

import hashlib
import hmac
import json
import secrets
import shutil
from datetime import datetime
from pathlib import Path

WORK = Path("integrity_demo")
WORK.mkdir(exist_ok=True)
(WORK / "a.txt").write_text("内容A", encoding="utf-8")
(WORK / "b.csv").write_text("1,2,3", encoding="utf-8")

MANIFEST_NAME = "manifest.json"


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def create_manifest(root: Path, key: bytes):
    """遍历目录生成摘要清单，并对清单整体签名。"""
    manifest = {
        "生成时间": datetime.now().isoformat(timespec="seconds"),
        "files": {
            f.name: file_sha256(f)
            for f in sorted(root.rglob("*"))
            if f.is_file() and f.name != MANIFEST_NAME
        },
    }
    payload = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
    signature = hmac.new(key, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    box = {"sig": signature, "manifest": manifest}
    (root / MANIFEST_NAME).write_text(
        json.dumps(box, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def verify_manifest(root: Path, key: bytes):
    """验签清单 → 逐文件比对摘要。"""
    box = json.loads((root / MANIFEST_NAME).read_text(encoding="utf-8"))
    payload = json.dumps(box["manifest"], ensure_ascii=False, sort_keys=True)
    actual_sig = hmac.new(key, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(actual_sig, box["sig"]):
        print("清单本身被篡改，结果不可信！")
        return
    ok = True
    for name, expected in box["manifest"]["files"].items():
        actual = file_sha256(root / name)
        status = "OK" if actual == expected else "已被篡改!"
        if actual != expected:
            ok = False
        print(f"  {name}: {status}")
    print("校验结论：", "全部完好" if ok else "发现问题文件")


KEY = secrets.token_bytes(32)      # 密钥只留在内存里，模拟“可信方”

print("== 1. 生成清单 ==")
create_manifest(WORK, KEY)
print((WORK / MANIFEST_NAME).read_text(encoding="utf-8")[:120], "...")

print("== 2. 首次校验 ==")
verify_manifest(WORK, KEY)

print("== 3. 模拟篡改 a.txt ==")
(WORK / "a.txt").write_text("内容A被改过", encoding="utf-8")
verify_manifest(WORK, KEY)

shutil.rmtree(WORK)     # 清理演示目录

# ===== 练习题 =====
# 1. 给工具增加“新增文件检测”：目录里多出的文件也要报警。
# 2. 把 KEY 改为从环境变量读取（第217课），写清缺失时的报错。
# 3. 思考：如果攻击者同时能改文件和重算签名（拿到 KEY），这个方案还剩什么价值？
