# Constants Reference (`game_fighter/constants.py`)

This module centralizes tunable values for sprite scaling, physics feel, and collision boxes. Everything scales from a base sprite size so the game can adjust visuals and physics together.

- `BASE_SPRITE_SCALE`: Reference sprite scale used when tuning speeds/physics. Changing this alters the baseline normalization for physics math.
- `SPRITE_SCALE`: Actual visual scale applied to sprites. Raising it makes characters larger on screen. Many other constants derive from this.
- `SCALE_FACTOR`: Ratio of `SPRITE_SCALE` to `BASE_SPRITE_SCALE`. Used to scale movement speeds and jump strength in `fighter.py` so they track sprite size.
- `PHYSICS_BASE_SCALE`: Baseline scale used to normalize physics feel across different sprite sizes.
- `PHYSICS_SCALE`: Multiplier combining `SCALE_FACTOR` and `PHYSICS_BASE_SCALE`; applied to gravity and other physics values in `game_widget.py` and `fighter.py` to keep movement grounded when sprite sizes change.
- `SPRITE_SIZE`: Reference pixel size (96 px) scaled by `SPRITE_SCALE`. Used for camera/layout calculations, stage margins, and initial fighter placement in `game_widget.py`.
- `HURTBOX_W`, `HURTBOX_H`: Dimensions (scaled) of the fighter hurtbox (the area that can be hit). Used in `fighter.py` for collision and in `game_widget.py` for debug rendering.
- `HITBOX_W`, `HITBOX_H`: Default attack hitbox size (scaled). Used in `fighter.py` when frame metadata doesn’t provide a custom hitbox, and drawn in `game_widget.py` for debug overlays.
- `STAGE_MARGIN`: Padding from screen edges used to clamp fighter positions in `game_widget.py` so characters don’t slide off-screen.
