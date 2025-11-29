BASE_SPRITE_SCALE = 2.0  # Reference scale for tuning speeds/physics
SPRITE_SCALE = 5  # Increase overall sprite size for better readability
SCALE_FACTOR = SPRITE_SCALE / BASE_SPRITE_SCALE
PHYSICS_BASE_SCALE = 5.0  # Baseline sprite scale used to normalize physics feel
PHYSICS_SCALE = SCALE_FACTOR * (PHYSICS_BASE_SCALE / max(1.0, float(SPRITE_SCALE)))
SPRITE_SIZE = int(96 * SPRITE_SCALE)

# Hurtbox roughly matches torso/legs, not the whole sprite outline
HURTBOX_W = int(48 * SPRITE_SCALE)   # tighter width to body
HURTBOX_H = int(84 * SPRITE_SCALE)   # slightly under full sprite height

# Attack hitbox tuned to fists/feet range
HITBOX_W = int(34 * SPRITE_SCALE)
HITBOX_H = int(32 * SPRITE_SCALE)

STAGE_MARGIN = 20  # Padding from screen edges for clamping
