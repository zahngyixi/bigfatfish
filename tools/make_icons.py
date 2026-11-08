# -*- coding: utf-8 -*-
"""
生成 PWA / APK 所需图标（无需设计软件）
用法: python tools/make_icons.py
依赖: Pillow (requirements.txt 已包含)
输出:
  bigfatfish/visual/assets/web/icons/icon-192.png
                                  icon-512.png
                                  icon-512-maskable.png
  android-webview/app/src/main/res/mipmap-*/ic_launcher.png
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
WEB_ICONS = ROOT / "bigfatfish" / "visual" / "assets" / "web" / "icons"
ANDROID_RES = ROOT / "android-webview" / "app" / "src" / "main" / "res"

SIZES = {
    "mdpi": 48, "hdpi": 72, "xhdpi": 96,
    "xxhdpi": 144, "xxxhdpi": 192,
}


def make_fish(size: int, maskable: bool = False) -> Image.Image:
    """绘制渐变背景 + 一条简洁的玻璃质感小鱼"""
    s = size
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    px = img.load()

    # 对角渐变背景
    for y in range(s):
        for x in range(s):
            t = (x + y) / (2 * s)
            r = int(20 + t * 60)
            g = int(40 + t * 110)
            b = int(90 + t * 130)
            px[x, y] = (r, g, b, 255)

    # 圆角 / 圆形裁切
    mask = Image.new("L", (s, s), 0)
    md = ImageDraw.Draw(mask)
    if maskable:
        # maskable 图标：内容留足安全区，整体铺满
        md.rectangle((0, 0, s, s), fill=255)
    else:
        md.rounded_rectangle((0, 0, s - 1, s - 1), radius=int(s * 0.22), fill=255)
    img.putalpha(mask)

    d = ImageDraw.Draw(img)
    k = s / 100.0
    # maskable 时把主体缩小到安全区
    if maskable:
        k *= 0.66
        ox, oy = s * 0.17, s * 0.17
    else:
        ox, oy = 0, 0

    def box(x0, y0, x1, y1):
        return (ox + x0 * k, oy + y0 * k, ox + x1 * k, oy + y1 * k)

    # 尾巴
    d.polygon([
        (ox + 70 * k, oy + 50 * k),
        (ox + 95 * k, oy + 28 * k),
        (ox + 88 * k, oy + 50 * k),
        (ox + 95 * k, oy + 72 * k),
    ], fill=(255, 255, 255, 190))
    # 身体
    d.ellipse(box(12, 28, 78, 74), fill=(255, 255, 255, 225),
              outline=(255, 255, 255, 255), width=max(1, int(1.5 * k)))
    # 高光
    d.ellipse(box(20, 34, 50, 48), fill=(255, 255, 255, 110))
    # 眼睛
    d.ellipse(box(28, 44, 37, 53), fill=(24, 32, 60, 255))
    d.ellipse(box(30, 45, 33, 48), fill=(255, 255, 255, 255))
    # 气泡
    for cx, cy, r in [(18, 16, 4), (26, 9, 2.6), (12, 24, 2)]:
        d.ellipse(box(cx - r, cy - r, cx + r, cy + r),
                  outline=(255, 255, 255, 170), width=max(1, int(k)))

    return img.filter(ImageFilter.GaussianBlur(max(0.3, s / 400)))


def main():
    WEB_ICONS.mkdir(parents=True, exist_ok=True)

    for name, size, maskable in [
        ("icon-192.png", 192, False),
        ("icon-512.png", 512, False),
        ("icon-512-maskable.png", 512, True),
    ]:
        make_fish(size, maskable).save(WEB_ICONS / name, "PNG")
        print(f"[OK] {WEB_ICONS / name}")

    for density, size in SIZES.items():
        out = ANDROID_RES / f"mipmap-{density}"
        out.mkdir(parents=True, exist_ok=True)
        make_fish(size, maskable=True).save(out / "ic_launcher.png", "PNG")
        make_fish(size, maskable=True).save(out / "ic_launcher_round.png", "PNG")
        print(f"[OK] {out / 'ic_launcher.png'}")

    print("\n[DONE] Icons generated")


if __name__ == "__main__":
    main()
