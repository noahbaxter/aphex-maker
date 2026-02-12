import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from rembg import remove
from scipy.ndimage import binary_dilation, gaussian_filter

from aphex_maker.config import get_prep_config


def remove_background(img: Image.Image, expand_pct: float = 0) -> Image.Image:
    # Get the raw mask from rembg
    mask = remove(img, only_mask=True)
    mask_arr = np.array(mask, dtype=np.float64) / 255.0

    # Expand the mask to keep more borderline pixels
    # expand is a percentage of the image's shorter dimension
    if expand_pct > 0:
        px = max(1, int(min(mask_arr.shape) * expand_pct / 100))
        binary = mask_arr > 0.1
        binary = binary_dilation(binary, iterations=px)
        mask_arr = gaussian_filter(binary.astype(np.float64), sigma=px / 2)
        mask_arr = np.clip(mask_arr, 0, 1)

    # Apply mask to original image
    img_rgba = img.convert("RGBA")
    img_arr = np.array(img_rgba)
    # Resize mask to match image in case rembg returns different dimensions
    if mask_arr.shape != (img_arr.shape[0], img_arr.shape[1]):
        from PIL import Image as _Image
        mask_resized = _Image.fromarray((mask_arr * 255).astype(np.uint8))
        mask_resized = mask_resized.resize((img_arr.shape[1], img_arr.shape[0]), _Image.LANCZOS)
        mask_arr = np.array(mask_resized, dtype=np.float64) / 255.0
    img_arr[:, :, 3] = (mask_arr * 255).astype(np.uint8)
    return Image.fromarray(img_arr)


def crop_to_content(img: Image.Image, padding: int = 0) -> Image.Image:
    alpha = img.split()[3]
    bbox = alpha.getbbox()
    if bbox is None:
        return img

    left, top, right, bottom = bbox
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(img.width, right + padding)
    bottom = min(img.height, bottom + padding)

    return img.crop((left, top, right, bottom))


def process_one(input_path: Path, output_path: Path, args):
    print(f"loading: {input_path}", file=sys.stderr)
    from PIL import ImageOps
    img = ImageOps.exif_transpose(Image.open(input_path)).convert("RGBA")

    print(f"  removing background (expand={args.expand})...", file=sys.stderr)
    img = remove_background(img, expand_pct=args.expand)

    if not args.no_crop:
        print("  cropping to subject...", file=sys.stderr)
        img = crop_to_content(img, padding=args.padding)

    print(f"  saving: {output_path} ({img.width}x{img.height})", file=sys.stderr)
    img.save(str(output_path), "PNG")


def main():
    cfg = get_prep_config()

    parser = argparse.ArgumentParser(
        prog="aphex-prep",
        description="Remove background from image and crop to subject.",
    )
    parser.add_argument("inputs", nargs="+", help="Input image(s) (PNG, JPEG, etc.)")
    parser.add_argument("-o", "--output", help="Output PNG path (only valid with single input)")
    parser.add_argument("--padding", type=int, default=cfg.get("padding", 10))
    parser.add_argument("--no-crop", action="store_true", default=not cfg.get("crop", True))
    parser.add_argument("--expand", type=int, default=cfg.get("expand", 0), help="Expand mask by N pixels to keep more of the image (default: 0)")

    args = parser.parse_args()

    if args.output and len(args.inputs) > 1:
        print("error: -o/--output can only be used with a single input file", file=sys.stderr)
        sys.exit(1)

    for input_str in args.inputs:
        input_path = Path(input_str)
        if not input_path.exists():
            print(f"error: input file not found: {input_path}", file=sys.stderr)
            sys.exit(1)

        if args.output:
            output_path = Path(args.output)
        else:
            out_dir = input_path.parent / "out"
            out_dir.mkdir(exist_ok=True)
            output_path = out_dir / (input_path.stem + "_prep.png")
        process_one(input_path, output_path, args)

    print("done.", file=sys.stderr)
