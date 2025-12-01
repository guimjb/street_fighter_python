# Sprite Anim (`game_fighter/sprite_anim.py`)

`SpriteAnim` slices sprite sheets into frames, advances animations over time, and exposes UVs and frame metadata for rendering and collision. It is used by `Fighter` to drive character animations and hit/hurt box metadata.

## Class: `SpriteAnim`

### Attributes
- `sheets`: Dict mapping state name -> sheet config (`tex`, `rects`, `fps`, optional `durations`, optional `meta`).
- `state`: Current animation state name.
- `frame`: Float frame index (allows smooth progression across frames).
- `loop`: Whether the current animation should loop.
- `flip_x`: Mirror flag; flips UVs horizontally when True.
- Internal caches: `_tex`, `_rects`, `_fps`, `_frame_durations`, `_frame_meta` for the active state.

### Methods
- `add_sheet_by_count(state, filepath, frame_count, frame_h=None, fps=6, row_y_px=0, frame_w=None, frame_step=None, start_x=0, frame_xs=None, frame_ws=None)`: Adds an animation sheet by slicing a texture evenly or via explicit x positions/widths. Sets texture filters to nearest when available. Used by `Fighter._load_sprites` when frame metadata isn’t precomputed.
- `add_sheet_from_frames(state, filepath, frames, fps=6, frame_durations=None)`: Adds an animation using explicit frame rects (`frames` list of dicts with x/y/w/h and optional metadata). Optionally accepts per-frame durations to override fps. Used by `Fighter._load_sprites` when JSON frame metadata exists.
- `play(state, loop=True, restart=False)`: Switches to a state, caching its texture/rects/fps/meta and resetting the frame counter. Called by `Fighter` whenever the target animation changes.
- `update(dt)`: Advances `frame` based on fps or per-frame durations; respects looping vs. clamping to the last frame. Called each game tick in `Fighter.update`.
- `finished() -> bool`: Returns True if a non-looping animation has reached its final frame. Used in `Fighter.pick_anim` to keep playing attack anims until done.
- `current_texture() -> Texture|None`: Returns the active texture for the current state. Used by `game_widget` when drawing fighters.
- `current_frame_index() -> int`: Clamped integer index of the current frame. Used by hitbox heuristics in `Fighter.attack_hitbox`.
- `current_frame_size() -> (w, h)`: Size of the current frame in source pixels. Used for collision boxes and layout.
- `current_frame_rect() -> (x, y, w, h)`: Source rect of the current frame. Used for debugging or custom slicing.
- `current_frame_meta() -> dict`: Metadata dict for the current frame (e.g., `hitbox`/`hurtbox` offsets) if provided by `add_sheet_from_frames`. Used by `Fighter` collision helpers.
- `current_texcoords() -> tuple`: Returns UV coordinates for the current frame, slightly inset to avoid bleeding, flipped horizontally if `flip_x` is True. Consumed by `game_widget` to update fighter rectangles on screen.
