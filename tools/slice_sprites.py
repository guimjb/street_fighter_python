"""
Auto-slice sprite sheets into frame rectangles by detecting empty columns between frames.

Assumptions:
- Frames are laid out horizontally on a single row.
- Transparency (alpha=0) separates frames (at least 1 empty column).

Outputs a JSON with entries per file:
{
  "Idle.png": {"w":191,"h":82,"frames":[{"x":0,"y":0,"w":48,"h":82}, ...]},
  ...
}

Usage:
    python3 tools/slice_sprites.py --folder "assets/ryu_sprites_project" --out ryu_frames.json
    python3 tools/slice_sprites.py --folder "assets/ken_sprites_project" --out ken_frames.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

from PIL import Image


def slice_sheet(path: Path, alpha_threshold: int = 1) -> Dict:
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    pixels = img.load()

    # Find columns that are fully transparent
    empty_cols = []
    for x in range(w):
        col_empty = True
        for y in range(h):
            if pixels[x, y][3] > alpha_threshold:
                col_empty = False
                break
        if col_empty:
            empty_cols.append(x)

    # Determine frame boundaries by scanning and splitting on empty columns
    frames: List[Dict[str, int]] = []
    x = 0
    while x < w:
        # Skip leading empty columns
        while x < w and x in empty_cols:
            x += 1
        if x >= w:
            break
        start = x
        while x < w and x not in empty_cols:
            x += 1
        end = x  # first empty after content
        frame_w = end - start
        if frame_w <= 0:
            continue
        frames.append({"x": start, "y": 0, "w": frame_w, "h": h})

    return {"w": w, "h": h, "frames": frames}


def main():
    parser = argparse.ArgumentParser(description="Auto-slice sprite sheets laid out horizontally.")
    parser.add_argument("--folder", required=True, help="Folder containing PNG sheets.")
    parser.add_argument("--out", required=True, help="Output JSON path.")
    parser.add_argument("--alpha-threshold", type=int, default=1, help="Alpha > threshold counts as opaque.")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.exists():
        raise SystemExit(f"Folder not found: {folder}")

    result = {}
    for png in sorted(folder.glob("*.png")):
        result[png.name] = slice_sheet(png, alpha_threshold=args.alpha_threshold)

    out_path = Path(args.out)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"Wrote {out_path} with {len(result)} sheets.")


if __name__ == "__main__":
    main()
