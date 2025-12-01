import json
import os
import random

from game_fighter.constants import PHYSICS_SCALE, SCALE_FACTOR, SPRITE_SCALE, SPRITE_SIZE, STAGE_MARGIN
from game_fighter.sprite_anim import SpriteAnim

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
FRAME_CACHE = None


def _load_frame_cache():
    global FRAME_CACHE
    if FRAME_CACHE is not None:
        return FRAME_CACHE
    FRAME_CACHE = {}
    for name in ("ryu_frames.json", "ken_frames.json"):
        p = os.path.join(BASE_DIR, name)
        if not os.path.exists(p):
            continue
        try:
            with open(p, "r") as f:
                data = json.load(f)
                FRAME_CACHE.update(data)
        except Exception:
            continue
    return FRAME_CACHE


class Fighter:
    def __init__(self, x, y, sprite_paths, floor_y, stage_width, move_speed=None, jump_speed=None):
        # Position
        self.x = x
        self.y = y
        self.render_scale = SPRITE_SCALE  # scale used for drawing/collisions

        # Velocity
        self.vx = 0
        self.vy = 0

        base_speed = 420 * SCALE_FACTOR
        self.move_speed = move_speed if move_speed is not None else base_speed * 0.65
        self.jump_speed = jump_speed if jump_speed is not None else 980 * SCALE_FACTOR
        self.floor_y = floor_y
        self.stage_width = stage_width
        self.facing = 1  # 1 = right, -1 = left

        # Health
        self.hp = 100
        self.max_hp = 100

        # Sprites
        self.sprite = SpriteAnim()
        self._load_sprites(sprite_paths)

        # Attack logic
        self.attack = None
        # Slightly longer hitbox width for punch reach
        self.attack_cfg = dict(startup=0.08, active=0.30, recovery=0.22, w=160, h=48, dmg=10)

        # Drawable assigned externally
        self.rect = None

        # Hitstun / Knockback
        self.hitstun = 0.0
        self.knockback_vx = 0.0
        self.was_hit = False
        self.defeated = False
        self.victorious = False
        self.defeat_floor = self.floor_y
        self.defeat_gravity_multiplier = 0.4  # lighter gravity when defeated for floatier fall
        self.defeat_impact_count = 0
        self.defeat_landing_event = None  # "first" or "second" when floor is hit
        self.defeat_knock_dir = 1

    def _load_sprites(self, paths):
        frames = _load_frame_cache()

        def add_anim(state, key, fps, frame_count=None, frame_xs=None, frame_ws=None):
            file_path = paths[key]
            base = os.path.basename(file_path)
            frame_info = frames.get(base)
            if frame_info and frame_info.get("frames"):
                self.sprite.add_sheet_from_frames(state, file_path, frame_info["frames"], fps=fps)
            elif frame_xs or frame_ws:
                self.sprite.add_sheet_by_count(state, file_path, frame_count=frame_count, fps=fps, frame_xs=frame_xs, frame_ws=frame_ws)
            else:
                self.sprite.add_sheet_by_count(state, file_path, frame_count=frame_count, fps=fps)

        add_anim("idle", "idle", fps=6, frame_count=4)
        add_anim("run", "run", fps=12, frame_count=5)
        add_anim("jump", "jump", fps=8, frame_count=7, frame_xs=[0, 41, 82, 123, 164, 205, 246], frame_ws=[41, 41, 41, 41, 41, 41, 41])
        add_anim("attack", "attack", fps=8, frame_count=5, frame_xs=[0, 45, 104, 183, 227], frame_ws=[45, 57, 77, 57, 57])
        add_anim("hit", "hit", fps=8, frame_count=4)
        add_anim("defeat", "defeat", fps=4, frame_count=5, frame_xs=[0, 50, 127, 205, 282], frame_ws=[50, 78, 80, 77, 76])

        # Choose victory 1 or victory 2 (50/50 chance)
        victory_file = random.choice(paths["victory"])
        base_vic = os.path.basename(victory_file)
        frame_info = frames.get(base_vic)
        if frame_info and frame_info.get("frames"):
            self.sprite.add_sheet_from_frames("victory", victory_file, frame_info["frames"], fps=6)
        else:
            self.sprite.add_sheet_by_count("victory", victory_file, frame_count=3, fps=6)

        self.sprite.play("idle")

    def reload_sprites(self, sprite_paths):
        """Swap the sprite sheets used by this fighter without recreating the object."""
        self.sprite = SpriteAnim()
        self._load_sprites(sprite_paths)

    def on_hit(self):
        """Trigger hit reaction animation."""
        self.was_hit = True
        self.sprite.play("hit", loop=False, restart=True)

    def on_defeat(self):
        """Trigger defeat animation and halt attacks."""
        self.defeated = True
        self.victorious = False
        self.attack = None
        self.vx = 0  # still allow knockback_vx to move the body
        # Land on the playable floor (keep a tiny allowance, not the screen bottom)
        self.defeat_floor = max(0, self.floor_y - 10)
        # Give a small downward impulse so the fall starts immediately
        self.vy = -abs(self.jump_speed) * 0.1
        self.defeat_impact_count = 0
        self.defeat_landing_event = None
        self.sprite.play("defeat", loop=False, restart=True)

    def on_victory(self):
        """Trigger victory animation."""
        self.victorious = True
        self.defeated = False
        self.attack = None
        self.vx = 0
        self.sprite.play("victory", loop=True, restart=True)

    # ---------------------------
    # COLLISION HELPERS
    # ---------------------------
    def _frame_size_world(self):
        fw, fh = self.sprite.current_frame_size()
        return fw * self.render_scale, fh * self.render_scale

    def _frame_box_from_meta(self, key):
        meta = self.sprite.current_frame_meta()
        if not meta or key not in meta:
            return None
        raw = meta[key]
        if isinstance(raw, dict):
            bx = raw.get("x", 0)
            by = raw.get("y", 0)
            bw = raw.get("w", 0)
            bh = raw.get("h", 0)
        elif isinstance(raw, (list, tuple)) and len(raw) == 4:
            bx, by, bw, bh = raw
        else:
            return None
        # Normalize if values are 0..1
        fw_px, fh_px = self.sprite.current_frame_size()
        if max(abs(bx), abs(by), bw, bh) <= 1.0:
            bx *= fw_px
            bw *= fw_px
            by *= fh_px
            bh *= fh_px
        return (bx, by, bw, bh)

    def _mirror_box(self, box, frame_w_px):
        if self.facing == 1:
            return box
        bx, by, bw, bh = box
        return (frame_w_px - (bx + bw), by, bw, bh)

    def _box_to_world(self, box):
        bx, by, bw, bh = box
        return (
            self.x + bx * self.render_scale,
            self.y + by * self.render_scale,
            bw * self.render_scale,
            bh * self.render_scale,
        )

    # ---------------------------
    # MOVEMENT / PHYSICS
    # ---------------------------
    def move_left(self):
        self.vx = -self.move_speed
        self.facing = -1

    def move_right(self):
        self.vx = self.move_speed
        self.facing = 1

    def stop(self):
        self.vx = 0

    def jump(self):
        if self.y <= self.floor_y + 0.5:
            self.vy = self.jump_speed

    def update_position(self, dt):
        self.x += self.vx * dt

    def apply_gravity(self, gravity, dt):
        self.vy += gravity * dt
        self.y += self.vy * dt

        if self.y < self.floor_y:
            self.y = self.floor_y
            self.vy = 0

    # ---------------------------
    # ATTACKS
    # ---------------------------
    def start_attack(self):
        if self.attack is None and not self.defeated:
            self.attack = dict(phase="startup", t=0, has_hit=False)
            self.sprite.play("attack", loop=False, restart=True)

    def attack_hitbox(self):
        if not self.attack:
            return None

        fw_px, fh_px = self.sprite.current_frame_size()
        meta_box = self._frame_box_from_meta("hitbox")
        if meta_box:
            box_px = self._mirror_box(meta_box, fw_px)
            return self._box_to_world(box_px)

        # Heuristic fallback: tie hitbox to current frame size near front arm/leg
        fw, fh = self._frame_size_world()
        state = self.sprite.state or ""
        frame_idx = self.sprite.current_frame_index()
        # Attack frames: extend further as the animation progresses
        if state == "attack":
            phase = 0.0
            total_frames = max(1, len(self.sprite.sheets.get("attack", {}).get("rects", [])))
            if total_frames > 1:
                phase = min(1.0, frame_idx / float(total_frames - 1))
            hit_w = fw * (0.32 + 0.18 * phase)
            hit_h = fh * 0.34
            # push forward as phase advances
            forward = 0.18 + 0.18 * phase
        else:
            hit_w = fw * 0.32
            hit_h = fh * 0.30
            forward = 0.12

        center_x = self.x + fw * 0.5 + (fw * forward if self.facing == 1 else -fw * forward)
        px = center_x - hit_w * 0.5
        py = self.y + fh * 0.30
        return (px, py, hit_w, hit_h)

    def hurtbox(self):
        fw_px, fh_px = self.sprite.current_frame_size()
        meta_box = self._frame_box_from_meta("hurtbox")
        if meta_box:
            box_px = self._mirror_box(meta_box, fw_px)
            return self._box_to_world(box_px)

        # Heuristic fallback centered on the sprite rect (better than fixed constants)
        fw, fh = self._frame_size_world()
        hb_w = fw * 0.68
        hb_h = fh * 0.9
        px = self.x + (fw - hb_w) / 2
        py = self.y + fh * 0.02
        return (px, py, hb_w, hb_h)

    def update_attack(self, dt):
        if not self.attack:
            return

        a = self.attack
        cfg = self.attack_cfg
        a["t"] += dt

        if a["phase"] == "startup":
            if a["t"] >= cfg["startup"]:
                a["phase"] = "active"
                a["t"] = 0

        elif a["phase"] == "active":
            if a["t"] >= cfg["active"]:
                a["phase"] = "recovery"
                a["t"] = 0

        elif a["phase"] == "recovery":
            if a["t"] >= cfg["recovery"]:
                self.attack = None

    # ---------------------------
    # ANIMATION
    # ---------------------------
    def pick_anim(self):
        on_ground = (self.y <= self.floor_y + 0.5) and abs(self.vy) < 1e-3

        if self.victorious:
            target = "victory"
            loop = True
        elif self.defeated:
            target = "defeat"
            loop = False
        elif self.hitstun > 0:
            target = "hit"
            loop = False
        elif self.attack and not self.sprite.finished():
            target = "attack"
            loop = False
        elif not on_ground:
            target = "jump"
            loop = True
        elif abs(self.vx) > 1:
            target = "run"
            loop = True
        else:
            target = "idle"
            loop = True

        self.sprite.flip_x = self.facing == -1

        if self.sprite.state != target:
            self.sprite.play(target, loop=loop)

    # ---------------------------
    # MAIN UPDATE
    # ---------------------------
    def update(self, dt, gravity):
        self.defeat_landing_event = None
        if self.victorious:
            # Stay in place, just animate
            self.vx = 0
            self.pick_anim()
            self.sprite.update(dt)
            return

        if self.defeated:
            prev_y = self.y
            # Let character fall to a lower floor with stronger gravity for dramatic effect
            # Still apply knockback motion on defeat
            self.x += self.knockback_vx * dt
            self.knockback_vx *= 0.9
            # Custom gravity so we can clamp to defeat_floor (a bit below ground)
            self.vy += gravity * self.defeat_gravity_multiplier * dt
            self.y += self.vy * dt
            landed = False
            if self.y < self.defeat_floor:
                self.y = self.defeat_floor
                landed = prev_y > self.defeat_floor
                self.vy = 0
            if landed and self.defeat_impact_count < 2:
                self.defeat_impact_count += 1
                if self.defeat_impact_count == 1:
                    self.defeat_landing_event = "first"
                    self.sprite.frame = 2  # show frame 3 on first slam
                    self.vy = self.jump_speed * 0.42  # small bounce to set up second hit
                elif self.defeat_impact_count == 2:
                    self.defeat_landing_event = "second"
                    self.sprite.frame = 4  # show frame 5 on final impact
                    self.knockback_vx = self.defeat_knock_dir * (900 * PHYSICS_SCALE)
                    self.vy = 0
            self._clamp_x()
            self.pick_anim()
            self.sprite.update(dt)
            return

        # If in hitstun, override normal movement
        if self.hitstun > 0:
            self.hitstun -= dt

            # Apply knockback motion
            self.x += self.knockback_vx * dt

            # Keep inside screen
            self._clamp_x()

            # Slowly reduce knockback (friction)
            self.knockback_vx *= 0.85

            self.apply_gravity(gravity, dt)

            # Keep inside screen (vertical impacts too)
            self._clamp_x()

            # When hitstun ends, stop forced movement
            if self.hitstun <= 0:
                self.knockback_vx = 0

            self.pick_anim()
            self.sprite.update(dt)
            return

        # Normal behavior
        self.update_position(dt)
        self.apply_gravity(gravity, dt)

        # Keep inside screen
        self._clamp_x()

        self.update_attack(dt)
        self.pick_anim()
        self.sprite.update(dt)

    def _clamp_x(self):
        scale_ratio = self.render_scale / float(SPRITE_SCALE)
        eff_size = SPRITE_SIZE * scale_ratio
        max_x = self.stage_width - eff_size - STAGE_MARGIN
        self.x = max(STAGE_MARGIN, min(max_x, self.x))
