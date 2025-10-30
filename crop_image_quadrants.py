#!/usr/bin/env python3
"""
Crop an image into 4 equal parts (quadrants).

Usage:
  python crop_image_quadrants.py /path/to/image.jpg -o /path/to/output

Options:
  -o, --output       Output directory (default: alongside the input image)
  --pad              If image dimensions are odd, pad to even before splitting
  --pad-color R G B  Padding color when using --pad (default: 0 0 0)

Outputs are named: <stem>_q00.<ext>, <stem>_q01.<ext>, <stem>_q10.<ext>, <stem>_q11.<ext>
where q(row)(col):
  q00 = top-left, q01 = top-right, q10 = bottom-left, q11 = bottom-right
"""

import argparse
import os
from pathlib import Path

import cv2
import numpy as np


def parse_args():
    parser = argparse.ArgumentParser(description="Crop an image into 4 equal quadrants")
    parser.add_argument("image", help="Path to input image")
    parser.add_argument("-o", "--output", help="Output directory (default: same as input image)")
    parser.add_argument("--pad", action="store_true", help="Pad to even dimensions if needed")
    parser.add_argument(
        "--pad-color",
        nargs=3,
        type=int,
        metavar=("R", "G", "B"),
        default=(0, 0, 0),
        help="Padding color as R G B (default: 0 0 0)",
    )
    return parser.parse_args()


def ensure_even_dimensions(image: np.ndarray, pad: bool, pad_color: tuple[int, int, int]) -> np.ndarray:
    height, width = image.shape[:2]
    need_pad_h = height % 2 != 0
    need_pad_w = width % 2 != 0

    if not (need_pad_h or need_pad_w):
        return image

    if not pad:
        raise ValueError(
            f"Image dimensions must be even to split equally: got {width}x{height}. "
            "Re-run with --pad to pad to even dimensions."
        )

    pad_bottom = 1 if need_pad_h else 0
    pad_right = 1 if need_pad_w else 0

    b, g, r = int(pad_color[2]), int(pad_color[1]), int(pad_color[0])
    padded = cv2.copyMakeBorder(
        image,
        top=0,
        bottom=pad_bottom,
        left=0,
        right=pad_right,
        borderType=cv2.BORDER_CONSTANT,
        value=(b, g, r),
    )
    return padded


def split_into_quadrants(image: np.ndarray) -> list[np.ndarray]:
    height, width = image.shape[:2]
    mid_y = height // 2
    mid_x = width // 2

    top_left = image[0:mid_y, 0:mid_x]
    top_right = image[0:mid_y, mid_x:width]
    bottom_left = image[mid_y:height, 0:mid_x]
    bottom_right = image[mid_y:height, mid_x:width]

    return [top_left, top_right, bottom_left, bottom_right]


def save_quadrants(quadrants: list[np.ndarray], input_path: Path, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = input_path.stem
    ext = input_path.suffix if input_path.suffix else ".png"

    names = [
        f"{stem}_q00{ext}",  # top-left
        f"{stem}_q01{ext}",  # top-right
        f"{stem}_q10{ext}",  # bottom-left
        f"{stem}_q11{ext}",  # bottom-right
    ]

    paths: list[Path] = []
    for quad, name in zip(quadrants, names):
        out_path = output_dir / name
        success = cv2.imwrite(str(out_path), quad)
        if not success:
            raise RuntimeError(f"Failed to write file: {out_path}")
        paths.append(out_path)
    return paths


def main():
    args = parse_args()

    input_path = Path(args.image)
    if not input_path.exists():
        raise FileNotFoundError(f"Input image not found: {input_path}")

    output_dir = Path(args.output) if args.output else input_path.parent

    image = cv2.imread(str(input_path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f"Could not read image: {input_path}")

    image = ensure_even_dimensions(image, pad=args.pad, pad_color=tuple(args.pad_color))

    quads = split_into_quadrants(image)
    out_paths = save_quadrants(quads, input_path, output_dir)

    print("Saved 4 tiles:")
    for p in out_paths:
        print(f"  - {p}")


if __name__ == "__main__":
    main()


