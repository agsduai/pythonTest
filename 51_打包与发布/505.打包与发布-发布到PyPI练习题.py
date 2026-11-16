# ===== 第505课：打包与发布-发布到PyPI =====
# 知识点：
#   - PyPI 是公共包仓库；TestPyPI 是演练场（数据独立、可随意删）
#   - 上传工具：twine（pip install twine），命令 `twine upload dist/*`
#   - 认证：API Token（用户名 __token__，密码是 token），不要用账号密码
#   - Token 放环境变量或 ~/.pypirc，绝不提交到 Git（第297/402课）
#   - 发布前必须：构建、本地安装验证、检查元数据、跑测试
#   - 发布后不能覆盖同版本；出问题只能发新版本（yank 只是隐藏）
#   - 本课不真的上传，演示完整本地校验流程与命令
# 依赖：setuptools / wheel / build（已安装）；twine 未安装也能学流程

import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

PYPROJECT = """
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "publish-demo-course"
version = "0.1.0"
description = "发布流程演示（不会真的上传）"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [{name = "课程学员", email = "student@example.com"}]
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
]

[tool.setuptools.packages.find]
where = ["src"]
"""

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    pkg = root / "src" / "publishdemo"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text('__version__ = "0.1.0"\n', encoding="utf-8")
    (root / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    (root / "README.md").write_text("# publish-demo\n\n发布流程演示。\n", encoding="utf-8")

    # ---- 1. 构建 ----
    print("== 1. 构建 ==")
    build = subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation"],
        cwd=root, capture_output=True, text=True,
    )
    print("  返回码：", build.returncode)
    artifacts = sorted((root / "dist").iterdir())
    for p in artifacts:
        print(f"  {p.name}（{p.stat().st_size:,} 字节）")

    # ---- 2. 元数据自检（相当于 twine check 的核心）----
    print("\n== 2. 元数据自检 ==")
    errors = []
    wheel = next(p for p in artifacts if p.suffix == ".whl")
    with zipfile.ZipFile(wheel) as zf:
        metadata_name = next(n for n in zf.namelist() if n.endswith("METADATA"))
        metadata = zf.read(metadata_name).decode("utf-8")
        fields = {}
        for line in metadata.splitlines():
            if ": " in line:
                key, value = line.split(": ", 1)
                fields.setdefault(key, value)

    required = ["Metadata-Version", "Name", "Version", "Summary", "Requires-Python"]
    for field in required:
        if field in fields:
            print(f"  ✓ {field}: {fields[field]}")
        else:
            errors.append(f"缺少 {field}")
            print(f"  ✗ 缺少 {field}")

    if fields.get("Description-Content-Type") is None:
        print("  提示：README 未声明内容类型，旧工具可能不识别 Markdown")

    # ---- 3. 本地安装验证 ----
    print("\n== 3. 本地安装验证 ==")
    target = root / "site"
    install = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--no-deps",
         "--target", str(target), str(wheel)],
        capture_output=True, text=True,
    )
    print("  安装返回码：", install.returncode)
    sys.path.insert(0, str(target))
    try:
        import publishdemo
        from importlib.metadata import version
        print("  导入成功，__version__ =", publishdemo.__version__)
        print("  importlib.metadata.version =", version("publish-demo-course"))
    finally:
        sys.path.remove(str(target))
        del sys.modules["publishdemo"]

    # ---- 4. 上传命令（演示，不执行）----
    print("\n== 4. 上传命令 ==")
    commands = [
        ("演练（TestPyPI）",
         "twine upload --repository testpypi dist/*"),
        ("正式（PyPI）",
         "twine upload dist/*"),
        ("验证安装",
         "pip install --index-url https://test.pypi.org/simple/ publish-demo-course"),
    ]
    for label, cmd in commands:
        print(f"  {label}：")
        print(f"    {cmd}")

    print("\n  认证配置（环境变量）：")
    print("    TWINE_USERNAME=__token__")
    print("    TWINE_PASSWORD=pypi-你的Token")
    print("  或 ~/.pypirc（注意文件权限，不要提交 Git）")

    print("\n== 5. 最终检查 ==")
    if errors:
        print("  存在问题：", errors)
    else:
        print("  ✓ 元数据完整，可以上传")

# ---- 发布流程 ----
print("\n== 发布流程 ==")
for step in [
    "1. 改版本号 + 更新 CHANGELOG（第502课）",
    "2. 跑全量测试（pytest）",
    "3. python -m build 生成 sdist + wheel",
    "4. 本地 pip install 验证（本课）",
    "5. twine upload --repository testpypi dist/* 演练",
    "6. 从 TestPyPI 安装验证",
    "7. twine upload dist/* 正式发布",
    "8. 打 Git tag 并推送（第474课）",
]:
    print("  ", step)

# ---- 安全注意 ----
print("\n== 安全注意 ==")
for item in [
    "Token 等同密码：只放环境变量/密钥管理，绝不写进代码",
    "发布前检查 wheel 里没有 .env、密钥、测试数据",
    "启用 2FA；为 CI 单独建 token 并限制权限",
    "不要上传公司内部代码到公共 PyPI（可用私有仓库）",
    "同版本不能覆盖：发布错了就发 0.1.1",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 安装 twine，运行 twine check dist/*。
# 2. 注册 TestPyPI，完整走一遍上传与安装（用测试包名）。
# 3. 给 METADATA 增加 project.urls，观察 wheel 元数据变化。
# 4. 思考：为什么 CI 里要用“发布 token”而不是个人账号密码？
