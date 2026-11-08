# -*- coding: utf-8 -*-
"""
大肥鱼 AI 伴侣 - 交付物自检脚本
用法: python tools/check_syntax.py
检查: Python 语法 / JSON 合法性 / 前端静态资源是否齐全
退出码: 0 = 全部通过, 1 = 有问题
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors = []
checked_py = 0
checked_json = 0

# ---------- Python ----------
for folder in ("bigfatfish", "tools"):
    base = ROOT / folder
    if not base.exists():
        continue
    for p in sorted(base.rglob("*.py")):
        try:
            ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
            checked_py += 1
        except SyntaxError as e:
            errors.append(f"[PY] {p.relative_to(ROOT)}:{e.lineno} {e.msg}")
        except Exception as e:
            errors.append(f"[PY] {p.relative_to(ROOT)}: {e}")

# ---------- JSON ----------
json_files = [
    "bigfatfish/visual/assets/web/manifest.json",
]
for rel in json_files:
    p = ROOT / rel
    if not p.exists():
        errors.append(f"[JSON] missing: {rel}")
        continue
    try:
        json.loads(p.read_text(encoding="utf-8"))
        checked_json += 1
    except Exception as e:
        errors.append(f"[JSON] {rel}: {e}")

# ---------- 前端静态资源 ----------
assets = [
    "bigfatfish/visual/assets/web/index.html",
    "bigfatfish/visual/assets/web/styles.css",
    "bigfatfish/visual/assets/web/app.js",
    "bigfatfish/visual/assets/web/sw.js",
    "bigfatfish/visual/assets/web/manifest.json",
    "bigfatfish/visual/assets/web/icons/icon-192.png",
    "bigfatfish/visual/assets/web/icons/icon-512.png",
    "bigfatfish/visual/assets/web/icons/icon-512-maskable.png",
]
for rel in assets:
    p = ROOT / rel
    if not p.exists():
        errors.append(f"[ASSET] missing: {rel}")
    elif p.stat().st_size == 0:
        errors.append(f"[ASSET] empty: {rel}")

# ---------- Android 壳工程 ----------
android_files = [
    "android-webview/settings.gradle",
    "android-webview/build.gradle",
    "android-webview/app/build.gradle",
    "android-webview/app/src/main/AndroidManifest.xml",
    "android-webview/app/src/main/java/com/bigfatfish/app/MainActivity.java",
    "android-webview/app/src/main/res/xml/network_security_config.xml",
    ".github/workflows/build-apk.yml",
]
for rel in android_files:
    if not (ROOT / rel).exists():
        errors.append(f"[ANDROID] missing: {rel}")

# ---------- 输出 ----------
print(f"[INFO] Python files parsed : {checked_py}")
print(f"[INFO] JSON files parsed   : {checked_json}")
print(f"[INFO] Assets checked      : {len(assets)}")
print(f"[INFO] Android files       : {len(android_files)}")

if errors:
    print(f"\n[FAIL] {len(errors)} problem(s):")
    for e in errors:
        print("  - " + e)
    sys.exit(1)

print("\n[PASS] All checks passed.")
sys.exit(0)
