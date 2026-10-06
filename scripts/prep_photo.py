"""Prep a photo for ASCII conversion.

Usage: python scripts/prep_photo.py source-photo.jpg

1. Remove the background with rembg so the subject is isolated.
2. Boost local contrast with CLAHE.
3. Composite onto pure white so the background maps to spaces.

Output: source-prepped.png
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/prep_photo.py <photo>")
        sys.exit(1)

    src = Path(sys.argv[1])
    if not src.exists():
        print(f"File not found: {src}")
        sys.exit(1)

    print(f"Removing background from {src} ...")
    with Image.open(src) as im:
        no_bg = remove(im)

    arr = np.array(no_bg)

    # Keep only RGB, build an alpha-based mask
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3] if arr.shape[2] == 4 else np.full(arr.shape[:2], 255, np.uint8)

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    print("Boosting contrast (CLAHE) ...")
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Composite onto pure white: masked-out areas become white (blank in ASCII)
    white = np.full_like(enhanced, 255)
    mask = alpha > 10
    white[mask] = enhanced[mask]

    out = src.with_name("source-prepped.png")
    cv2.imwrite(str(out), white)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
