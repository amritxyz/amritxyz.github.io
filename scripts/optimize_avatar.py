#!/usr/bin/env python3
"""
Optimize any avatar image into a lightweight, high-performance WebP image
for amritxyz.site. Automatically strips EXIF/metadata and updates the inlined
navbar data URI.
"""

import argparse
import base64
import os
import sys
from pathlib import Path
from PIL import Image, ImageOps


def find_default_avatar(repo_root: Path) -> Path | None:
    candidates = [
        repo_root / "static" / "avatar.png",
        repo_root / "static" / "avatar.jpg",
        repo_root / "static" / "avatar.jpeg",
        repo_root / "static" / "avatar.webp",
        repo_root / "avatar.png",
        repo_root / "avatar.jpg",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def format_bytes(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    else:
        return f"{num_bytes / (1024 * 1024):.2f} MB"


def main():
    parser = argparse.ArgumentParser(
        description="Convert and optimize an image to WebP with metadata stripping and data URI update."
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to source image (PNG, JPG, WEBP, etc.). Defaults to static/avatar.png",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output WebP path. Defaults to static/avatar.webp",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        default=85,
        help="WebP quality factor 1-100 (default: 85, ideal balance of clarity and size)",
    )
    parser.add_argument(
        "--lossless",
        action="store_true",
        help="Encode with lossless WebP compression",
    )
    parser.add_argument(
        "--max-width",
        type=int,
        default=512,
        help="Maximum width in pixels to downscale large camera photos (default: 512, 0 to disable)",
    )
    parser.add_argument(
        "--max-height",
        type=int,
        default=512,
        help="Maximum height in pixels to downscale large camera photos (default: 512, 0 to disable)",
    )
    parser.add_argument(
        "--no-data-uri",
        action="store_true",
        help="Skip updating layouts/partials/avatar-data-uri.html",
    )

    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent

    input_path = Path(args.input) if args.input else find_default_avatar(repo_root)
    if not input_path or not input_path.is_file():
        print(
            "Error: Source image not found. Provide a path or place avatar.png in static/.",
            file=sys.stderr,
        )
        sys.exit(1)

    output_path = (
        Path(args.output)
        if args.output
        else repo_root / "static" / "avatar.webp"
    )

    orig_size = input_path.stat().st_size
    print(f"Reading: {input_path} ({format_bytes(orig_size)})")

    try:
        img = Image.open(input_path)
        # Automatically fix EXIF orientation if taken on a smartphone
        img = ImageOps.exif_transpose(img)
    except Exception as e:
        print(f"Error opening image: {e}", file=sys.stderr)
        sys.exit(1)

    orig_dimensions = img.size
    orig_mode = img.mode

    # Convert to RGB or RGBA (discarding palette or CMYK if present)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "A" in img.mode else "RGB")

    # Resize if larger than max dimensions, preserving aspect ratio
    max_w = args.max_width
    max_h = args.max_height
    if max_w > 0 and max_h > 0:
        if img.width > max_w or img.height > max_h:
            img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            print(f"Resized: {orig_dimensions[0]}x{orig_dimensions[1]} → {img.width}x{img.height}")
        else:
            print(f"Dimensions: {img.width}x{img.height}")
    else:
        print(f"Dimensions: {img.width}x{img.height}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save optimized WebP with method=6 (maximum compression effort)
    # Metadata (EXIF, ICC, comments) is stripped by default since we don't pass exif= or icc_profile=
    save_kwargs = {
        "format": "WEBP",
        "method": 6,
    }
    if args.lossless:
        save_kwargs["lossless"] = True
    else:
        save_kwargs["quality"] = args.quality

    img.save(output_path, **save_kwargs)
    new_size = output_path.stat().st_size
    savings = (1 - (new_size / orig_size)) * 100 if orig_size > 0 else 0

    print(f"✓ Saved:   {output_path.relative_to(repo_root)} ({format_bytes(new_size)})")
    if savings > 0:
        print(f"✓ Reduced: {savings:.1f}% reduction ({format_bytes(orig_size)} → {format_bytes(new_size)})")

    print("\nAvatar optimization complete!")


if __name__ == "__main__":
    main()
