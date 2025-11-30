"""
Quick inspector for a sprite/font atlas. Finds connected non-transparent regions
and prints their bounding boxes so you can map UI pieces (e.g., health bars, font glyphs)
without manually slicing the PNG.

Usage:
    python3 tools/atlas_inspect.py --image "assets/text_and_health_bar/HealthFont.png"
"""

from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from PIL import Image


@dataclass
class Region:
    x: int
    y: int
    w: int
    h: int

    @property
    def area(self) -> int:
        return self.w * self.h

    def as_tuple(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.w, self.h)


def find_regions(img: Image.Image, alpha_threshold: int = 8, min_area: int = 4) -> List[Region]:
    """Return bounding boxes for connected components where alpha > threshold."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    alpha = img.split()[-1]
    w, h = img.size
    pix = alpha.load()
    visited = [[False] * h for _ in range(w)]

    regions: List[Region] = []

    def neighbors(px: int, py: int):
        if px > 0:
            yield (px - 1, py)
        if px + 1 < w:
            yield (px + 1, py)
        if py > 0:
            yield (px, py - 1)
        if py + 1 < h:
            yield (px, py + 1)

    for x in range(w):
        for y in range(h):
            if visited[x][y]:
                continue
            visited[x][y] = True
            if pix[x, y] <= alpha_threshold:
                continue

            # Flood-fill this component
            stack = deque()
            stack.append((x, y))
            min_x = max_x = x
            min_y = max_y = y

            while stack:
                cx, cy = stack.pop()
                for nx, ny in neighbors(cx, cy):
                    if visited[nx][ny]:
                        continue
                    visited[nx][ny] = True
                    if pix[nx, ny] <= alpha_threshold:
                        continue
                    stack.append((nx, ny))
                    if nx < min_x:
                        min_x = nx
                    elif nx > max_x:
                        max_x = nx
                    if ny < min_y:
                        min_y = ny
                    elif ny > max_y:
                        max_y = ny

            region = Region(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
            if region.area >= min_area:
                regions.append(region)

    # Stable sort top-to-bottom, then left-to-right
    regions.sort(key=lambda r: (r.y, r.x))
    return regions


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect non-transparent regions in an RGBA atlas.")
    parser.add_argument("--image", type=Path, required=True, help="Path to the RGBA atlas.")
    parser.add_argument("--alpha-threshold", type=int, default=8, help="Alpha > threshold counts as opaque.")
    parser.add_argument("--min-area", type=int, default=4, help="Ignore tiny specks below this area.")
    args = parser.parse_args()

    if not args.image.exists():
        raise SystemExit(f"Image not found: {args.image}")

    img = Image.open(args.image)
    regions = find_regions(img, alpha_threshold=args.alpha_threshold, min_area=args.min_area)

    print(f"Found {len(regions)} regions in {args.image} (w={img.size[0]}, h={img.size[1]}).")
    print("Format: x, y, w, h")
    for idx, r in enumerate(regions):
        print(f"{idx:02d}: {r.x}, {r.y}, {r.w}, {r.h}")


if __name__ == "__main__":
    main()
