#!/usr/bin/env python3
"""
Crop images in a directory into 4 equal parts (quadrants) each.

Usage:
  python crop_image_quadrants.py /path/to/images -o /path/to/output

Options:
  -o, --output       Output directory (default: same directory as the input images)

Odd width or height is padded by one black pixel (bottom/right) before splitting.

Outputs are named: <stem>_q00.<ext>, <stem>_q01.<ext>, <stem>_q10.<ext>, <stem>_q11.<ext>
where q(row)(col):
  q00 = top-left, q01 = top-right, q10 = bottom-left, q11 = bottom-right
"""

import argparse
from pathlib import Path

import cv2
import numpy as np

IMAGE_GLOBS = ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Crop all images in a directory into 4 equal quadrants each"
    )
    parser.add_argument("input_dir", help="Directory containing images to crop")
    parser.add_argument(
        "-o",
        "--output",
        help="Output directory (default: same directory as the input images)",
    )
    return parser.parse_args()


def collect_images(directory: Path) -> list[Path]:
    found: dict[Path, None] = {}
    for pattern in IMAGE_GLOBS:
        for path in directory.glob(pattern):
            found[path.resolve()] = None
    return sorted(found.keys())


def ensure_even_dimensions(image: np.ndarray) -> np.ndarray:
    height, width = image.shape[:2]
    need_pad_h = height % 2 != 0
    need_pad_w = width % 2 != 0

    if not (need_pad_h or need_pad_w):
        return image

    pad_bottom = 1 if need_pad_h else 0
    pad_right = 1 if need_pad_w else 0

    return cv2.copyMakeBorder(
        image,
        top=0,
        bottom=pad_bottom,
        left=0,
        right=pad_right,
        borderType=cv2.BORDER_CONSTANT,
        value=(0, 0, 0),
    )


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


def crop_image(input_path: Path, output_dir: Path) -> list[Path]:
    image = cv2.imread(str(input_path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f"Could not read image: {input_path}")

    image = ensure_even_dimensions(image)
    quads = split_into_quadrants(image)
    return save_quadrants(quads, input_path, output_dir)


def main():
    args = parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input must be an existing directory: {input_dir}")

    output_dir = Path(args.output) if args.output else input_dir

    image_paths = collect_images(input_dir)
    if not image_paths:
        raise FileNotFoundError(
            f"No images found in {input_dir} (supported: .jpg, .jpeg, .png)"
        )

    total_tiles = 0

    for input_path in image_paths:
        out_paths = crop_image(input_path, output_dir)
        total_tiles += len(out_paths)
        print(f"{input_path.name} -> 4 tiles:")
        for p in out_paths:
            print(f"  - {p}")

    print(f"\nProcessed {len(image_paths)} image(s), wrote {total_tiles} tile(s) to {output_dir}")


if __name__ == "__main__":
    main()
