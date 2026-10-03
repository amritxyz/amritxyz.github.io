#!/usr/bin/env python3
"""
Generate round favicons, apple-touch-icon, and data URIs for amritxyz.site.
Supports any input image (.png, .webp, .jpg, .jpeg, .avif, etc.).
"""

import argparse
import base64
import io
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps


def find_default_avatar(root_dir: Path) -> Path | None:
    candidates = [
        root_dir / "static" / "avatar.png",
        root_dir / "static" / "avatar.webp",
        root_dir / "static" / "avatar.jpg",
        root_dir / "avatar.png",
        root_dir / "avatar.webp",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None



def crop_to_circle(image, box=None, max_out=512):
    w, h = image.size
    if box:
        x0, y0, size = box
        if x0 < 0 or y0 < 0 or x0 + size > w or y0 + size > h:
            sys.exit(f"Crop box {box} is outside the {w}x{h} image")
    else:
        size = min(w, h)
        x0, y0 = (w - size) // 2, (h - size) // 2

    out = min(size, max_out)
    cropped = image.crop((x0, y0, x0 + size, y0 + size)).resize((out, out), Image.Resampling.LANCZOS)

    big = out * 4
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, big - 1, big - 1), fill=255)
    cropped.putalpha(mask.resize((out, out), Image.Resampling.LANCZOS))
    return cropped

def main():
    parser = argparse.ArgumentParser(
        description="Convert any image into circular favicons, apple touch icon, and inlined Data URIs."
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to input avatar/image (PNG, WEBP, JPG, etc.). If omitted, looks in static/avatar.*",
    )
    parser.add_argument(
        "--crop-x",
        type=int,
        default=None,
        help="Top-left X coordinate for square crop",
    )
    parser.add_argument(
        "--crop-y",
        type=int,
        default=None,
        help="Top-left Y coordinate for square crop",
    )
    parser.add_argument(
        "--crop-size",
        type=int,
        default=None,
        help="Square crop dimension in pixels",
    )
    parser.add_argument(
        "--no-navbar",
        action="store_true",
        help="Skip updating static/avatar.webp and navbar data URI",
    )

    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent

    input_path = Path(args.input) if args.input else find_default_avatar(repo_root)
    if not input_path or not input_path.is_file():
        print(
            "Error: Input image not found. Please provide an image path or place avatar.png in static/.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Processing source image: {input_path} ({input_path.stat().st_size // 1024} KB)")

    try:
        src = ImageOps.exif_transpose(Image.open(input_path)).convert("RGBA")
    except Exception as e:
        print(f"Error opening image {input_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # Check if specific crop requested, or if static/avatar.png known 512x376 crop
    crop_box = None
    if args.crop_x is not None and args.crop_y is not None and args.crop_size is not None:
        crop_box = (args.crop_x, args.crop_y, args.crop_size)
    elif src.size == (512, 376):
        # Optimized face center for the default avatar
        crop_box = (46, 0, 350)

    round_avatar = crop_to_circle(src, crop_box)

    static_dir = repo_root / "static"
    partials_dir = repo_root / "layouts" / "partials"
    static_dir.mkdir(parents=True, exist_ok=True)
    partials_dir.mkdir(parents=True, exist_ok=True)

    # 1. static/avatar-round.png
    avatar_round_path = static_dir / "avatar-round.png"
    round_avatar.save(avatar_round_path, format="PNG", optimize=True)
    print(f"✓ Saved {avatar_round_path.relative_to(repo_root)} ({avatar_round_path.stat().st_size} bytes)")

    # 2. static/favicon.ico (multi-resolution 16, 32, 48, 64)
    favicon_ico_path = static_dir / "favicon.ico"
    ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
    round_avatar.save(favicon_ico_path, format="ICO", sizes=ico_sizes)
    print(
        f"✓ Saved {favicon_ico_path.relative_to(repo_root)} (16x16, 32x32, 48x48, 64x64, {favicon_ico_path.stat().st_size} bytes)"
    )

    # 3. static/favicon.png (48x48 Google search specification)
    fav_48 = round_avatar.resize((48, 48), Image.Resampling.LANCZOS)
    fav_png_path = static_dir / "favicon.png"
    fav_48.save(fav_png_path, format="PNG", optimize=True)
    print(f"✓ Saved {fav_png_path.relative_to(repo_root)} (48x48, {fav_png_path.stat().st_size} bytes)")

    # 4. static/apple-touch-icon.png (180x180 iOS specification)
    fav_180 = round_avatar.resize((180, 180), Image.Resampling.LANCZOS)
    apple_path = static_dir / "apple-touch-icon.png"
    fav_180.save(apple_path, format="PNG", optimize=True)
    print(f"✓ Saved {apple_path.relative_to(repo_root)} (180x180, {apple_path.stat().st_size} bytes)")

    # 5. Navbar WebP avatar
    if not args.no_navbar:
        avatar_webp_path = static_dir / "avatar.webp"
        src.save(avatar_webp_path, format="WEBP", quality=85, method=6)
        print(f"✓ Saved {avatar_webp_path.relative_to(repo_root)} ({avatar_webp_path.stat().st_size} bytes)")

    print("\nAll assets successfully generated!")


if __name__ == "__main__":
    main()
