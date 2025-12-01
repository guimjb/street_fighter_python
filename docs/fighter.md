# Fighter (`game_fighter/fighter.py`)

`Fighter` models a single combatant: movement, gravity, attacks, hit/hurt boxes, animation selection, and defeat/victory states. This file also loads per-frame metadata for sprite slicing.

## Module-level helpers
- `_load_frame_cache() -> dict`: Lazily loads `ryu_frames.json` and `ken_frames.json` from the repo root and caches the merged frame metadata. Used by `_load_sprites` to configure `SpriteAnim`. Returns the shared cache; callers rely on it to avoid re-reading files.

## Class: `Fighter`
Constructor signature:
`Fighter(x, y, sprite_paths, floor_y, stage_width, move_speed=None, jump_speed=None)`

Parameters:
- `x`, `y`: Starting world-space position for the sprite origin.
- `sprite_paths`: Dict of sprite sheet file paths keyed by state (`idle`, `run`, `jump`, `attack`, `hit`, `defeat`, `victory`).
- `floor_y`: Y position of the playable floor; used to clamp jumps/falls.
- `stage_width`: Width of the stage for horizontal clamping.
- `move_speed` (optional): Override for horizontal speed; defaults to 420 * `SCALE_FACTOR` * 0.65.
- `jump_speed` (optional): Override for jump impulse; defaults to 980 * `SCALE_FACTOR`.

Key attributes created: position (`x`, `y`), velocity (`vx`, `vy`), facing, health, `sprite` (`SpriteAnim`), attack state, knockback/hitstun data, defeat/victory flags, and a `rect` placeholder assigned externally for drawing.

### Sprite loading
- `_load_sprites(paths)`: Builds animation sheets on `self.sprite` using frame metadata from `_load_frame_cache`. Sets up idle/run/jump/attack/hit/defeat/victory animations and plays `idle` to start.
- `reload_sprites(sprite_paths)`: Reinitializes `self.sprite` with new sheets (used when swapping characters). No return; callers (e.g., `game_widget.py` during character select) depend on this to change a fighter’s look without recreating the object.

### State change hooks
- `on_hit()`: Marks the fighter as hit and plays the `hit` animation once. No return; used by collision resolution in `game_widget.py` when a hitbox connects.
- `on_defeat()`: Marks defeat, clears attacks, zeroes horizontal input velocity, sets a defeat floor slightly below ground, seeds a downward impulse, resets landing counters, and plays `defeat` once. Called when HP drops to 0 in `game_widget.py` hit handling.
- `on_victory()`: Marks victory, clears attacks, zeroes velocity, and loops `victory`. Called when the opponent is defeated.

### Collision helpers
- `_frame_size_world() -> (w, h)`: Current frame size scaled by `render_scale`. Used by hit/hurt box fallbacks.
- `_frame_box_from_meta(key) -> tuple|None`: Reads `hitbox`/`hurtbox` from current frame metadata, normalizing 0..1 values to pixels. Used by `attack_hitbox`/`hurtbox`.
- `_mirror_box(box, frame_w_px) -> tuple`: Mirrors a box horizontally if facing left. Called by hit/hurt box generators.
- `_box_to_world(box) -> (x, y, w, h)`: Converts sprite-local box to world coordinates using `render_scale`. Used after mirroring to place boxes in the scene.

### Movement / physics
- `move_left()`, `move_right()`: Set `vx` and facing accordingly. Called by input/AI.
- `stop()`: Zeroes `vx` (used when no directional input).
- `jump()`: If on/near the floor, applies `jump_speed` to `vy`. Called by input/AI.
- `update_position(dt)`: Applies horizontal velocity over `dt`.
- `apply_gravity(gravity, dt)`: Integrates gravity, applies to `vy`/`y`, and clamps to `floor_y`. Used by `update`.

### Attacks and boxes
- `start_attack()`: If not already attacking/defeated, seeds an attack state (`startup` phase) and plays the `attack` animation. Called by input/AI.
- `attack_hitbox() -> (x, y, w, h)|None`: Returns the active attack hitbox in world space when attacking. Prefers per-frame `hitbox` metadata; otherwise builds a heuristic box that advances with the animation. Used by `game_widget.py` to test collisions.
- `hurtbox() -> (x, y, w, h)`: Returns the current hurtbox in world space. Uses metadata when present, otherwise a heuristic body-sized box. Used for collision checks and debug draw.
- `update_attack(dt)`: Advances attack phases (startup → active → recovery) based on `attack_cfg` timers, clearing `self.attack` when done. Called each frame in `update`.

### Animation selection
- `pick_anim()`: Chooses the animation to play based on victory/defeat, hitstun, attack state, airborne/grounded, and horizontal speed. Flips sprites when facing left and starts a new animation when the target state changes. Called in `update`.

### Main update
- `update(dt, gravity)`: Core per-frame update.
  - Handles victory (idle animation only), defeat (custom gravity, bounce, landing events), hitstun (knockback, gravity, friction), or normal flow (movement, gravity, attack update).
  - Calls `_clamp_x()` to keep within stage bounds.
  - Calls `pick_anim()` and advances `self.sprite`.
  - Sets `defeat_landing_event` to `"first"`/`"second"` on defeat impacts, read by `game_widget.py` to trigger screen shake.

### Bounds
- `_clamp_x()`: Uses `render_scale`, `SPRITE_SIZE`, and `STAGE_MARGIN` to keep `x` within the stage width. Called in `update` and defeat/hitstun flows to prevent fighters leaving the screen.
