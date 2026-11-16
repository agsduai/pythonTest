# ===== 第502课：打包与发布-版本管理 =====
# 知识点：
#   - 语义化版本：MAJOR.MINOR.PATCH（破坏性/新增功能/修复）
#   - 预发布：1.0.0a1、1.0.0b2、1.0.0rc1；开发版 1.0.0.dev1
#   - 单一事实来源：版本号只在一处定义（__version__ 或 pyproject）
#   - 读取版本：importlib.metadata.version("包名")（安装后）
#   - 发版流程：改版本 → 跑测试 → 构建 → 打 tag → 上传
#   - 与第474课 Git tag、第500课 pyproject 的配合
# 依赖：无

import re
from pathlib import Path
import tempfile

SEMVER = re.compile(
    r"^(?P<major>0|[1-9]\d*)\."
    r"(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<pre>[0-9A-Za-z.-]+))?$"
)


def parse_version(version: str) -> dict:
    match = SEMVER.match(version)
    if not match:
        raise ValueError(f"不是合法的语义化版本：{version!r}")
    result = match.groupdict()
    for key in ("major", "minor", "patch"):
        result[key] = int(result[key])
    return result


def bump(version: str, part: str = "patch") -> str:
    v = parse_version(version)
    if part == "major":
        return f"{v['major'] + 1}.0.0"
    if part == "minor":
        return f"{v['major']}.{v['minor'] + 1}.0"
    if part == "patch":
        return f"{v['major']}.{v['minor']}.{v['patch'] + 1}"
    raise ValueError("part 必须是 major/minor/patch")


print("== 语义化版本解析 ==")
for version in ("1.2.3", "0.1.0", "2.0.0-rc.1", "1.0.0-alpha.2"):
    try:
        print(f"  {version:16s} → {parse_version(version)}")
    except ValueError as exc:
        print(f"  {version:16s} → 错误：{exc}")

print("\n== 版本递增 ==")
current = "1.2.3"
print("  当前：", current)
for part in ("patch", "minor", "major"):
    print(f"  bump {part:5s} → {bump(current, part)}")

# ---- 预发布与排序 ----
print("\n== 预发布版本 ==")
versions = ["1.0.0.dev1", "1.0.0a1", "1.0.0b1", "1.0.0rc1", "1.0.0"]
print("  发布顺序：", " < ".join(versions))
print("  说明：dev < alpha < beta < rc < 正式版")

# ---- 单一事实来源 ----
print("\n== 单一事实来源 ==")
with tempfile.TemporaryDirectory() as tmp:
    pkg = Path(tmp) / "versionpkg"
    pkg.mkdir()
    version_file = pkg / "_version.py"
    version_file.write_text('__version__ = "1.2.3"\n', encoding="utf-8")
    (pkg / "__init__.py").write_text(
        "from ._version import __version__\n"
        "__all__ = [\"__version__\"]\n",
        encoding="utf-8",
    )

    import sys
    sys.path.insert(0, tmp)
    try:
        import versionpkg
        print("  __init__ 读取：", versionpkg.__version__)
    finally:
        sys.path.remove(tmp)
        for name in list(sys.modules):
            if name.startswith("versionpkg"):
                del sys.modules[name]

    # 发版脚本：bump 后写回
    new_version = bump("1.2.3", "minor")
    version_file.write_text(f'__version__ = "{new_version}"\n', encoding="utf-8")
    print("  bump 后写回：", version_file.read_text(encoding="utf-8").strip())

# ---- 安装后读取版本 ----
print("\n== 安装后读取版本 ==")
try:
    from importlib.metadata import version, PackageNotFoundError
    for package in ("pip", "setuptools", "wheel", "build"):
        try:
            print(f"  {package:12s} {version(package)}")
        except PackageNotFoundError:
            print(f"  {package:12s} 未安装")
except Exception as exc:
    print("  读取失败：", exc)

# ---- 发版检查清单 ----
print("\n== 发版检查清单 ==")
for item in [
    "1. 确认要发的类型（major/minor/patch）并改版本号",
    "2. 更新 CHANGELOG（新增/修复/破坏性变更）",
    "3. 跑全量测试（第212/214课）",
    "4. 构建 wheel 与 sdist（第504课）",
    "5. 本地安装验证（第505课）",
    "6. 打 Git tag（第474课）并推送",
    "7. 上传 TestPyPI 验证，再传正式 PyPI",
    "8. 记录发布信息，保留上一个版本可回滚",
]:
    print("  ", item)

# ---- 常见坑 ----
print("\n== 常见坑 ==")
for item in [
    "版本号多处定义导致不一致 → 单一来源",
    "发布后不能覆盖同名同版本（PyPI 不允许）→ 出错就发新补丁版",
    "0.x 版本可以随意破坏兼容，但要在文档里说清",
    "预发布版不会被 pip 默认安装（需要 --pre）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给 parse_version 增加对 1.0.0+build.5 的支持。
# 2. 写脚本 read_version(path) 从 _version.py 正则提取版本号。
# 3. 实现 compare_versions(a, b)，比较两个语义化版本大小。
# 4. 思考：为什么 PyPI 不允许覆盖已发布的版本？
