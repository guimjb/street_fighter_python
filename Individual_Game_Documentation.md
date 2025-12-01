# Individual Game Documentation — Fighter Game

## Overview
A 2D fighting prototype built with Kivy featuring sprite‑sheet animation, basic movement,
a single attack with hit detection, parallax background, rounds, and victory/defeat banners.

## Algorithms and Data Structures
- **Sprite animation**: integer rectangles (x, y, w, h) over a single‑row sheet. Texture coordinates computed from `uvpos/uvsize` and frame rects.
- **Movement and physics**: Euler integration on position/velocity; vertical gravity; floor clamp at `floor_y`.
- **Facing**: updated from last horizontal input, used to position attack hitbox and to flip sprite UVs.
- **Hit detection**: axis‑aligned bounding boxes (AABB) for player attack vs. enemy placeholder hurtbox.
- **Rounds**: best‑of‑3; end of round triggers banner and resets; end of match shows persistent banner.
- **Parallax**: multi‑layer parallax with bounded offset and small overscan to avoid exposing edges.

## Key Implementation Points
- **`SpriteAnim`**:
  - `add_sheet_by_count(...)` slices the sheet by frame count with rounded boundaries to avoid drift.
  - `current_texcoords()` maps frame rects through texture `uvpos/uvsize` and supports horizontal flip.
- **Attack state machine**:
  - Phases: `startup → active → recovery`; timers tracked per frame; hitbox only during active.
- **Parallax layout**:
  - Layers sorted so lower‑numbered files draw first (farther back).
  - `overscan` expands scale slightly and `max_offset` bounds horizontal shift.
- **Robustness**:
  - Update loop wrapped in try/except; prints traceback on error.

## Assets
- Character: `assets/kobold/with_outline/{IDLE.png,RUN.png,"ATTACK 1.png"}`
- Background: `assets/forest/Background layers/*.png`

## Known Limitations / Next Steps
- Enemy AI and combat interactions are placeholders.
- No camera or stage bounds beyond window clamping.
- Unified system integration (menu + consistent controls) pending (see Integration Plan).

## Recent Changes
- HUD now uses a shared health bar: P1 drains left→center, P2 right→center; both names/pips remain visible. Timer sits below the centered bar.
- Narrator VO added for round intros (round + number/final callouts), fight start (with 0.5s buffer after the intro), perfect rounds, win/lose outcomes, and match continue.
- Fight overlay now shows every round and stays up for the duration of `fight.mp3` before play resumes.
- Prebuilt Android APK checked into the repo root (`streetfightherpython.apk`) for quick sideloading.
