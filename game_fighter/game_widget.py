import os
import random

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, InstructionGroup, Ellipse, PushMatrix, PopMatrix, Scale, Translate, Line
from kivy.graphics.texture import Texture
from kivy.uix.widget import Widget

from game_fighter.constants import SPRITE_SIZE, HURTBOX_W, HURTBOX_H, SCALE_FACTOR, SPRITE_SCALE, PHYSICS_SCALE
from game_fighter.fighter import Fighter
from game_fighter.input_manager import InputManager

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

SPECIAL_KEYS = {32: "space", 273: "up", 274: "down", 275: "right", 276: "left"}


def keyname_from_event(keycode: int, codepoint: str) -> str:
    if codepoint and codepoint.strip():
        return codepoint.lower()
    if keycode in SPECIAL_KEYS:
        return SPECIAL_KEYS[keycode]
    if 32 <= keycode < 127:
        return chr(keycode).lower()
    return str(keycode)


def keyname_from_keyup(keycode: int) -> str:
    if 32 <= keycode < 127:
        return chr(keycode).lower()
    return SPECIAL_KEYS.get(keycode, str(keycode))


def load_ryu_assets():
    folder = os.path.join(ASSETS_DIR, "ryu_sprites_project")
    return {
        "idle": os.path.join(folder, "Idle.png"),
        "run": os.path.join(folder, "Walk.png"),
        "jump": os.path.join(folder, "Jump.png"),
        "attack": os.path.join(folder, "right_punch.png"),
        "hit": os.path.join(folder, "Hit.png"),
        "defeat": os.path.join(folder, "Defeat.png"),
        "victory": [
            os.path.join(folder, "victory_1.png"),
            os.path.join(folder, "victory_2.png"),
        ],
    }


def load_ken_assets():
    folder = os.path.join(ASSETS_DIR, "ken_sprites_project")
    return {
        "idle": os.path.join(folder, "idle_ken.png"),
        "run": os.path.join(folder, "Walking_Ken.png"),
        "jump": os.path.join(folder, "ken_jump.png"),
        "attack": os.path.join(folder, "ken_right_punch.png"),
        "hit": os.path.join(folder, "ken_hit.png"),
        "defeat": os.path.join(folder, "ken_defeat.png"),
        "victory": [
            os.path.join(folder, "ken_victory_1.png"),
            os.path.join(folder, "ken_victory_2.png"),
        ],
    }


DEBUG_MODE = os.environ.get("FIGHTER_DEBUG", "0") == "1"


class FighterGame(Widget):
    def __init__(self, **kwargs):
        # Debug flag: skip idle screen and start playing immediately when enabled
        self.debug_mode = kwargs.pop("debug_mode", DEBUG_MODE)

        super().__init__(**kwargs)

        # Stage bounds (fixed so resizing the window doesn't move fighters)
        w, _ = Window.size
        self.stage_width = w or 1280
        # Controls
        self.control_modes = ["keyboard", "touch"]
        # Default to touch controls so mobile devices start with on-screen buttons
        self.selected_control_mode_index = self.control_modes.index("touch") if "touch" in self.control_modes else 0
        # Input
        self.input = InputManager()
        self.touch_actions = {}  # touch.id -> set(actions)
        self._pending_jump = False
        self._pending_attack = False
        self.touch_group = InstructionGroup()
        self.touch_button_boxes = {}
        self._main_menu_play_rect = None
        self._main_menu_control_rect = None
        self.show_hitboxes = False  # Toggle debug overlays on/off (default hidden)

        # Physics
        self.gravity = -2200 * PHYSICS_SCALE
        self.floor_y = 90
        self.floor_height = 90
        self.floor_texture = None
        self.floor_base_w = None
        self.floor_base_h = None
        font_candidate = os.path.join(ASSETS_DIR, "Fonts", "StreetFont.ttf")
        self.font_path = font_candidate if os.path.exists(font_candidate) else None
        self.hp_back_tex = self._load_texture(os.path.join(ASSETS_DIR, "Menu", "healthbar_back.png"))
        self.hp_front_tex = self._load_texture(os.path.join(ASSETS_DIR, "Menu", "healthbar_front.png"))
        self.round_timer = 60
        self._timer_accum = 0.0

        # Round state
        self.state = "playing" if self.debug_mode else "main_menu"
        self.round = 1
        self.p1_wins = 0
        self.p2_wins = 0
        self.max_wins = 2
        # UI / selection
        self.character_options = [
            {"name": "Ryu", "loader": load_ryu_assets, "portrait": os.path.join(ASSETS_DIR, "ryu_sprites_project", "RyuPortrait.png")},
            {"name": "Ken", "loader": load_ken_assets, "portrait": os.path.join(ASSETS_DIR, "ken_sprites_project", "ken_portrait.png")},
        ]
        self.base_width = 1920
        self.base_height = 1080
        self.stage_options = [
            {"name": "Boat", "key": "boat"},
            {"name": "Military", "key": "military"},
        ]
        self.selected_character_index = 0
        self.selected_stage_index = 0
        self.current_stage_key = self.stage_options[self.selected_stage_index]["key"]
        self.p1_name = "P1"
        self.p2_name = "P2"

        # Drawables
        self.fx = InstructionGroup()
        self.banner_group = InstructionGroup()
        self.ui_group = InstructionGroup()
        self.hud_group = InstructionGroup()
        self.hp1_base = None
        self.hp1_bar = None
        self.hp2_base = None
        self.hp2_bar = None
        self.timer_rect = None
        self.timer_color = None
        self.p1_name_rect = None
        self.p2_name_rect = None
        self.p1_name_color = None
        self.p2_name_color = None
        self.p1_round_colors = []
        self.p1_round_ellipses = []
        self.p2_round_colors = []
        self.p2_round_ellipses = []
        self.portrait_cache = {}
        self.base_width = 1920
        self.base_height = 1080

        # Background
        self.bg_layers = []
        self._load_stage(self.current_stage_key)

        # Create fighters
        self._init_fighters()
        self._apply_sprite_scale()

        # Camera transform (applied to world)
        self.camera_scale = 1.4  # restore previous zoom for 16:9
        self.transform_before = InstructionGroup()
        self.transform_after = InstructionGroup()
        self.canvas.before.add(self.transform_before)
        self.cam_x = 0.0
        self.cam_y = 0.0
        self.camera_smooth = 0.15  # 0..1 smoothing toward target
        self.shake_time = 0.0
        self.shake_duration = 0.0
        self.shake_strength = 0.0
        self.shake_offset = (0.0, 0.0)
        # Debug overlays (world-space)
        self.hitbox_debug = InstructionGroup()
        self.hurtbox_debug = InstructionGroup()

        # Scene
        self._build_scene()
        self.bind(size=self._on_size)

        Window.bind(on_key_down=self._on_key_down)
        Window.bind(on_key_up=self._on_key_up)
        Window.bind(on_joy_axis=self._on_joy_axis)
        Window.bind(on_joy_hat=self._on_joy_hat)
        Window.bind(on_joy_button_down=self._on_joy_button_down)
        Window.bind(on_joy_button_up=self._on_joy_button_up)

        Clock.schedule_interval(self.update, 1 / 60)

        # Attach render layers in correct order
        self._attach_after_layers()
        self._ai_timer = 0.0
        self._ai_action = None

        # Show main menu or jump straight into play for debugging
        if self.debug_mode:
            self._reset_round_data()
            self.state = "playing"
            self._show_banner("DEBUG MODE", seconds=0.6, font_px=48)
        else:
            self._enter_main_menu()
        self._layout_touch_ui()

    # --------------------------------------------------------
    # LOAD CHARACTER SPRITES + CREATE P1/P2
    # --------------------------------------------------------

    def _init_fighters(self):
        # Player = Ryu
        ryu_paths = load_ryu_assets()

        # Bot = Ken
        ken_paths = load_ken_assets()

        p1_x, p2_x = self._start_positions()
        self.p1 = Fighter(p1_x, self.floor_y, ryu_paths, self.floor_y, stage_width=self.stage_width)
        self.p2 = Fighter(p2_x, self.floor_y, ken_paths, self.floor_y, stage_width=self.stage_width)

    # --------------------------------------------------------
    # STAGE LOADING
    # --------------------------------------------------------
    def _make_layer(self, path, idx, total, *, align="center", bottom=False, speed=None, is_floor=False, y_offset=0, scale_mode="fit_width", ref_w=None):
        tex = CoreImage(path).texture
        try:
            tex.mag_filter = "nearest"
            tex.min_filter = "nearest"
        except Exception:
            pass
        depth = idx / max(1, total - 1)
        speed = speed if speed is not None else (0.10 + 0.45 * depth)
        return {
            "tex": tex,
            "rect": None,
            "w": tex.size[0],
            "h": tex.size[1],
            "speed": speed,
            "align": align,
            "bottom": bottom,
            "is_floor": is_floor,
            "y_offset": y_offset,
            "scale_mode": scale_mode,
            "ref_w": ref_w,
        }

    def _reference_floor_y(self):
        """Use Military stage floor as reference for collision height across stages."""
        ref_w, ref_h = 1024, 176
        ratio = 0.2
        win_w = Window.size[0] or 1280
        scale = win_w / ref_w
        return max(10, ref_h * scale * ratio)

    def _refresh_floor_scale(self):
        """Recompute floor height/offset when the window size changes."""
        if not self.floor_base_w or not self.floor_base_h:
            return
        scale = (self.width or Window.size[0] or 1280) / max(1, self.floor_base_w)
        self.floor_height = self.floor_base_h * scale
        self.floor_y = self._reference_floor_y()
        # Update background bottom offsets that depend on floor height
        for layer in self.bg_layers:
            if not layer.get("is_floor") and layer.get("bottom"):
                layer["y_offset"] = self.floor_height

    def _load_stage(self, key):
        # Default floor + background
        self.floor_texture = None
        self.floor_height = 90
        self.floor_y = self.floor_height
        self.bg_ref_w = None

        layers = []
        if key == "boat":
            folder = os.path.join(ASSETS_DIR, "boat_stage_project")
            floor_path = os.path.join(folder, "boat_stage_floor.png")
            if os.path.exists(floor_path):
                tex = CoreImage(floor_path).texture
                try:
                    tex.mag_filter = "nearest"
                    tex.min_filter = "nearest"
                except Exception:
                    pass
                self.floor_texture = tex
                self.floor_base_w, self.floor_base_h = tex.size
                scale = (Window.size[0] or 1280) / max(1, self.floor_base_w)
                self.floor_height = self.floor_base_h * scale
                self.floor_y = self._reference_floor_y()
            # Backgrounds, align left; BG2 sits slightly above the floor
            files = [
                "boat_stage_background.png",  # far
                "boat_stage_background_2.png",  # mid
            ]
            files = [os.path.join(folder, f) for f in files if os.path.exists(os.path.join(folder, f))]
            for i, fpath in enumerate(files):
                if i == 0:
                    y_off = self.floor_height
                else:
                    y_off = self.floor_height + 10
                layer = self._make_layer(
                    fpath,
                    i,
                    len(files),
                    align="left",
                    bottom=True,
                    y_offset=y_off,
                    scale_mode="shared",
                    ref_w=self.bg_ref_w,
                )
                if self.bg_ref_w is None:
                    self.bg_ref_w = layer["w"]
                    layer["ref_w"] = self.bg_ref_w
                layers.append(layer)
            if self.floor_texture:
                layers.append(
                    self._make_layer(
                        floor_path,
                        len(layers),
                        len(layers) + 1,
                        align="left",
                        bottom=True,
                        speed=0.0,
                        is_floor=True,
                    )
                )

        elif key == "military":
            folder = os.path.join(ASSETS_DIR, "military_stage_project")
            bg_path = os.path.join(folder, "stage_military_background.png")
            if os.path.exists(bg_path):
                layers.append(self._make_layer(bg_path, 0, 1))

            floor_path = os.path.join(folder, "stage_military_floor.png")
            if os.path.exists(floor_path):
                tex = CoreImage(floor_path).texture
                try:
                    tex.mag_filter = "nearest"
                    tex.min_filter = "nearest"
                except Exception:
                    pass
                self.floor_texture = tex
                self.floor_base_w, self.floor_base_h = tex.size
                scale = (Window.size[0] or 1280) / max(1, self.floor_base_w)
                self.floor_height = self.floor_base_h * scale
                self.floor_y = self._reference_floor_y()
                layers.append(
                    self._make_layer(
                        floor_path,
                        len(layers),
                        len(layers) + 1,
                        align="center",
                        bottom=True,
                        speed=0.0,
                        is_floor=True,
                    )
                )

        if not layers:
            # Minimal 1x1 neutral texture fallback so rendering still works without assets
            tex = Texture.create(size=(1, 1), colorfmt="rgba")
            tex.blit_buffer(b"\x20\x3a\x5a\xff", colorfmt="rgba", bufferfmt="ubyte")
            tex.mag_filter = "nearest"
            tex.min_filter = "nearest"
            layers.append({"tex": tex, "rect": None, "w": 1, "h": 1, "speed": 0.1})

        self.bg_layers = layers

    def _layout_bg_cover(self):
        win_w, win_h = self.width, self.height
        if win_w <= 1 or win_h <= 1:
            return

        px_norm = max(0.0, min(1.0, self.p1.x / max(1.0, self.stage_width)))

        for layer in self.bg_layers:
            tex = layer["tex"]
            lw, lh = layer["w"], layer["h"]
            spd = 0.0  # parallax disabled
            rect = layer["rect"]

            scale_mode = layer.get("scale_mode", "fit_width")
            ref_w = layer.get("ref_w")
            if scale_mode == "shared" and ref_w:
                scale = win_w / max(1, ref_w)
                sw, sh = lw * scale, lh * scale
            elif scale_mode == "fit_width" and not layer.get("is_floor"):
                # Cover the viewport to avoid letterboxing (fills height if taller)
                scale = max(win_w / max(1, lw), win_h / max(1, lh))
                sw, sh = lw * scale, lh * scale
            elif scale_mode == "fit_width":
                scale = win_w / max(1, lw)
                sw, sh = win_w, lh * scale
            else:
                scale = 1.0
                sw, sh = lw, lh

            align = layer.get("align", "center")
            if align == "left":
                base_x = 0
            elif align == "right":
                base_x = win_w - sw
            else:
                base_x = (win_w - sw) / 2

            if layer.get("bottom"):
                base_y = 0
            else:
                base_y = (win_h - sh) / 2
                # If cover scaling exceeds height, allow slight upward bias to remove top gaps
                if sh >= win_h:
                    base_y = min(0, base_y)

            offset = 0

            pos = (base_x + offset, base_y + layer.get("y_offset", 0))
            size = (sw, sh)

            if rect is None:
                with self.canvas:
                    layer["rect"] = Rectangle(texture=tex, pos=pos, size=size)
            else:
                rect.pos = pos
                rect.size = size

    # --------------------------------------------------------
    # DRAW SCENE
    # --------------------------------------------------------
    def _build_scene(self):
        self.canvas.clear()
        for layer in self.bg_layers:
            layer["rect"] = None
        self._layout_bg_cover()

        p1_fw, p1_fh = self.p1.sprite.current_frame_size()
        p2_fw, p2_fh = self.p2.sprite.current_frame_size()
        p1_sw = p1_fw * self.p1.render_scale
        p1_sh = p1_fh * self.p1.render_scale
        p2_sw = p2_fw * self.p2.render_scale
        p2_sh = p2_fh * self.p2.render_scale

        with self.canvas:
            # Invisible ground plane; floor art is drawn separately on top of background
            Color(0, 0, 0, 0)
            self.ground = Rectangle(pos=(0, 0), size=(self.width, self.floor_height))

            # Fighters
            Color(1, 1, 1, 1)
            self.p1.rect = Rectangle(texture=self.p1.sprite.current_texture(), pos=(self.p1.x, self.p1.y), size=(p1_sw, p1_sh))
            self.p2.rect = Rectangle(texture=self.p2.sprite.current_texture(), pos=(self.p2.x, self.p2.y), size=(p2_sw, p2_sh))

        # Ensure world/overlay/UI layers are attached in correct order
        if self.fx not in self.canvas.after.children:
            self.canvas.after.add(self.fx)
        if self.hud_group not in self.canvas.after.children:
            self.canvas.after.add(self.hud_group)
        if self.banner_group not in self.canvas.after.children:
            self.canvas.after.add(self.banner_group)
        self._attach_after_layers()

        self._build_hud()
        self._sync_draw()

    def _on_size(self, *args):
        self.stage_width = self.width or self.stage_width
        self._apply_sprite_scale()
        self._refresh_floor_scale()
        if hasattr(self, "p1"):
            self.p1.stage_width = self.stage_width
        if hasattr(self, "p2"):
            self.p2.stage_width = self.stage_width
        if self.ground:
            self.ground.size = (self.width, self.floor_height)
            self.ground.pos = (0, 0)
        self._layout_hud()
        self._layout_bg_cover()
        self._sync_draw()
        self._render_current_ui()
        self._layout_touch_ui()

    def _attach_after_layers(self):
        """Attach canvas.after layers in draw order so HUD/UI are not camera-transformed."""
        after = self.canvas.after
        groups = [
            self.hitbox_debug,  # world-space debug
            self.hurtbox_debug,  # world-space debug
            self.fx,  # world fx in world space
            self.transform_after,  # PopMatrix for camera/shake
            self.touch_group,
            self.hud_group,  # HUD/UI after pop
            self.banner_group,
            self.ui_group,
        ]
        for g in groups:
            if g in after.children:
                after.remove(g)
        for g in groups:
            after.add(g)

    def _compute_sprite_scale(self):
        # Keep fighters at their native SPRITE_SCALE regardless of window size
        return SPRITE_SCALE

    def _apply_sprite_scale(self):
        scale = self._compute_sprite_scale()
        if hasattr(self, "p1"):
            self.p1.render_scale = scale
        if hasattr(self, "p2"):
            self.p2.render_scale = scale

    def _sync_draw(self):
        self._update_camera()
        # Update fighter 1
        if self.p1.rect:
            frame_w, frame_h = self.p1.sprite.current_frame_size()
            sw = frame_w * self.p1.render_scale
            sh = frame_h * self.p1.render_scale
            self.p1.rect.pos = (self.p1.x, self.p1.y)
            self.p1.rect.size = (sw, sh)
            tex = self.p1.sprite.current_texture()
            if self.p1.rect.texture is not tex:
                self.p1.rect.texture = tex
            self.p1.rect.tex_coords = self.p1.sprite.current_texcoords()
        # Update fighter 2
        if self.p2.rect:
            frame_w, frame_h = self.p2.sprite.current_frame_size()
            sw = frame_w * self.p2.render_scale
            sh = frame_h * self.p2.render_scale
            self.p2.rect.pos = (self.p2.x, self.p2.y)
            self.p2.rect.size = (sw, sh)
            tex = self.p2.sprite.current_texture()
            if self.p2.rect.texture is not tex:
                self.p2.rect.texture = tex
            self.p2.rect.tex_coords = self.p2.sprite.current_texcoords()

    def _draw_debug_boxes(self):
        if not self.show_hitboxes:
            self.hitbox_debug.clear()
            self.hurtbox_debug.clear()
            return

        self.hitbox_debug.clear()
        self.hurtbox_debug.clear()

        # DRAW HURTBOXES (BLUE)
        Color(0.2, 0.4, 1, 0.4)
        for f in (self.p1, self.p2):
            x, y, w, h = f.hurtbox()
            self.hurtbox_debug.add(Rectangle(pos=(x, y), size=(w, h)))

        # DRAW HITBOXES (RED)
        Color(1, 0.2, 0.2, 0.4)
        for f in (self.p1, self.p2):
            hb = f.attack_hitbox()
            if hb:
                x, y, w, h = hb
                self.hitbox_debug.add(Rectangle(pos=(x, y), size=(w, h)))

    # --------------------------------------------------------
    # HUD (HEALTH / TIMER / NAMES)
    # --------------------------------------------------------
    def _build_hud(self):
        self.hud_group.clear()
        use_textures = self.hp_back_tex is not None and self.hp_front_tex is not None
        self.bar_height = 80  # fallback height if textures are missing
        # Base bars (background)
        if use_textures:
            self.hud_group.add(Color(1, 1, 1, 1))
            self.hp1_base = Rectangle(texture=self.hp_back_tex)
            self.hud_group.add(self.hp1_base)
            self.hud_group.add(Color(1, 1, 1, 1))
            self.hp2_base = Rectangle(texture=self.hp_back_tex)
            self.hud_group.add(self.hp2_base)
        else:
            self.hud_group.add(Color(0.65, 0.1, 0.1, 1))
            self.hp1_base = Rectangle()
            self.hud_group.add(self.hp1_base)
            self.hud_group.add(Color(0.65, 0.1, 0.1, 1))
            self.hp2_base = Rectangle()
            self.hud_group.add(self.hp2_base)

        # Foreground bars (fill)
        if use_textures:
            self.hud_group.add(Color(1, 1, 1, 1))
            self.hp1_bar = Rectangle(texture=self.hp_front_tex)
            self.hud_group.add(self.hp1_bar)
            self.hud_group.add(Color(1, 1, 1, 1))
            self.hp2_bar = Rectangle(texture=self.hp_front_tex)
            self.hud_group.add(self.hp2_bar)
        else:
            self.hud_group.add(Color(0.98, 0.9, 0.1, 1))
            self.hp1_bar = Rectangle()
            self.hud_group.add(self.hp1_bar)
            self.hud_group.add(Color(0.98, 0.9, 0.1, 1))
            self.hp2_bar = Rectangle()
            self.hud_group.add(self.hp2_bar)

        # Timer
        self.timer_color = Color(1, 1, 1, 1)
        self.timer_rect = Rectangle()
        self.hud_group.add(self.timer_color)
        self.hud_group.add(self.timer_rect)

        # Names
        self.p1_name_color = Color(1, 1, 1, 1)
        self.p1_name_rect = Rectangle()
        self.hud_group.add(self.p1_name_color)
        self.hud_group.add(self.p1_name_rect)

        self.p2_name_color = Color(1, 1, 1, 1)
        self.p2_name_rect = Rectangle()
        self.hud_group.add(self.p2_name_color)
        self.hud_group.add(self.p2_name_rect)

        # Round counters (2 per side)
        ball_count = 2
        self.p1_round_colors = []
        self.p1_round_ellipses = []
        for _ in range(ball_count):
            c = Color(0.65, 0.1, 0.1, 1)
            e = Ellipse()
            self.p1_round_colors.append(c)
            self.p1_round_ellipses.append(e)
            self.hud_group.add(c)
            self.hud_group.add(e)

        self.p2_round_colors = []
        self.p2_round_ellipses = []
        for _ in range(ball_count):
            c = Color(0.65, 0.1, 0.1, 1)
            e = Ellipse()
            self.p2_round_colors.append(c)
            self.p2_round_ellipses.append(e)
            self.hud_group.add(c)
            self.hud_group.add(e)

        self._layout_hud()
        self._render_timer()
        self._render_names()
        self._render_round_counters()
        self._render_round_counters()

    def _layout_hud(self):
        if not self.hp1_base or not self.width:
            return
        center_x = self.width / 2
        gap = max(60, self.width * 0.05)
        half_w = min(self.width * 0.36 * 1.5, 760 * 1.5)  # 50% wider bars
        bar_h = self._health_bar_height(half_w)
        self.bar_height = bar_h
        top_margin = self.height - bar_h * 1.5  # leave 50% bar height offset from top
        ratio_p1 = max(0.0, min(1.0, self.p1.hp / self.p1.max_hp))
        ratio_p2 = max(0.0, min(1.0, self.p2.hp / self.p2.max_hp))

        # Bases anchored to center gap
        self.hp1_base.pos = (center_x - gap / 2 - half_w, top_margin)
        self.hp1_base.size = (half_w, bar_h)
        self.hp2_base.pos = (center_x + gap / 2, top_margin)
        self.hp2_base.size = (half_w, bar_h)

        # Foreground bars shrink toward center
        p1_w = half_w * ratio_p1
        p2_w = half_w * ratio_p2
        self.hp1_bar.pos = (center_x - gap / 2 - p1_w, top_margin)
        self.hp1_bar.size = (p1_w, bar_h)
        self.hp2_bar.pos = (center_x + gap / 2, top_margin)
        self.hp2_bar.size = (p2_w, bar_h)

        if self.hp_back_tex:
            self.hp1_base.texture = self.hp_back_tex
            self.hp1_base.tex_coords = self._health_texcoords(self.hp_back_tex, 1.0, anchor="right")
            self.hp2_base.texture = self.hp_back_tex
            self.hp2_base.tex_coords = self._health_texcoords(self.hp_back_tex, 1.0, anchor="left")

        if self.hp_front_tex:
            self.hp1_bar.texture = self.hp_front_tex
            self.hp1_bar.tex_coords = self._health_texcoords(self.hp_front_tex, ratio_p1, anchor="right")
            self.hp2_bar.texture = self.hp_front_tex
            self.hp2_bar.tex_coords = self._health_texcoords(self.hp_front_tex, ratio_p2, anchor="left")

        # Timer in the gap, centered vertically on the bar
        self._render_timer(top_margin, bar_h, gap)
        self._render_names(top_margin)
        self._render_round_counters(top_margin)

    def _render_timer(self, top_margin=None, bar_h=None, gap=None):
        if top_margin is None:
            top_margin = self.height - self.bar_height * 1.5
        if bar_h is None:
            bar_h = getattr(self, "bar_height", 20)
        if gap is None:
            gap = max(60, self.width * 0.05)

        txt = str(max(0, int(self.round_timer)))
        lbl = CoreLabel(text=txt, **self._label_kwargs(72))
        lbl.refresh()
        tex = lbl.texture
        x = (self.width - tex.width) / 2
        y = top_margin + (bar_h - tex.height) / 2
        self.timer_rect.texture = tex
        self.timer_rect.pos = (x, y)
        self.timer_rect.size = tex.size

    def _render_names(self, top_margin=None):
        if top_margin is None:
            top_margin = self.height - self.bar_height * 1.5
        font_px = 72

        bar_h = self.bar_height
        ball_d = self.bar_height * 0.7
        pip_y = top_margin - ball_d - 20

        # P1 name centered in its health bar
        lbl1 = CoreLabel(text=self.p1_name, **self._label_kwargs(font_px))
        lbl1.refresh()
        tex1 = lbl1.texture
        x1 = self.hp1_base.pos[0] + (self.hp1_base.size[0] - tex1.width) / 2
        y1 = pip_y + (ball_d - tex1.height) / 2
        self.p1_name_rect.texture = tex1
        self.p1_name_rect.pos = (x1, y1)
        self.p1_name_rect.size = tex1.size

        # P2 name centered in its health bar
        lbl2 = CoreLabel(text=self.p2_name, **self._label_kwargs(font_px))
        lbl2.refresh()
        tex2 = lbl2.texture
        x2 = self.hp2_base.pos[0] + (self.hp2_base.size[0] - tex2.width) / 2
        y2 = pip_y + (ball_d - tex2.height) / 2
        self.p2_name_rect.texture = tex2
        self.p2_name_rect.pos = (x2, y2)
        self.p2_name_rect.size = tex2.size

    def _render_round_counters(self, top_margin=None):
        if top_margin is None:
            top_margin = self.height - self.bar_height * 1.5
        ball_d = self.bar_height * 0.7
        gap = ball_d * 0.2
        y = top_margin - ball_d - 20

        # P1 aligned to left edge of bar
        start_x1 = self.hp1_base.pos[0]
        for idx, (c, e) in enumerate(zip(self.p1_round_colors, self.p1_round_ellipses)):
            c.rgba = (0.98, 0.9, 0.1, 1) if idx < self.p1_wins else (0.65, 0.1, 0.1, 1)
            e.pos = (start_x1 + idx * (ball_d + gap), y)
            e.size = (ball_d, ball_d)

        # P2 aligned to right edge of bar
        start_x2 = self.hp2_base.pos[0] + self.hp2_base.size[0] - ball_d
        for idx, (c, e) in enumerate(zip(self.p2_round_colors, self.p2_round_ellipses)):
            c.rgba = (0.98, 0.9, 0.1, 1) if idx < self.p2_wins else (0.65, 0.1, 0.1, 1)
            e.pos = (start_x2 - idx * (ball_d + gap), y)
            e.size = (ball_d, ball_d)

    def _update_health_bars(self):
        if not self.hp1_bar:
            return
        self._layout_hud()

    def _health_bar_height(self, half_w):
        if self.hp_back_tex:
            aspect = self.hp_back_tex.size[1] / max(1.0, float(self.hp_back_tex.size[0]))
            # Keep height in a readable range while preserving texture aspect ratio.
            return max(32, min(self.height * 0.18, half_w * aspect))
        return getattr(self, "bar_height", 80)

    @staticmethod
    def _health_texcoords(tex, ratio, anchor="left"):
        ratio = max(0.0, min(1.0, ratio))
        u0, v0 = tex.uvpos
        us, vs = tex.uvsize
        if anchor == "right":
            u_start = u0 + us * (1.0 - ratio)
            u_end = u0 + us
        else:
            u_start = u0
            u_end = u0 + us * ratio
        v_start = v0
        v_end = v0 + vs
        return (u_start, v_start, u_end, v_start, u_end, v_end, u_start, v_end)
    # --------------------------------------------------------
    # MENU / UI HELPERS
    # --------------------------------------------------------
    def _clear_ui(self):
        self.ui_group.clear()

    def _load_texture(self, path):
        if not path or not os.path.exists(path):
            return None
        tex = CoreImage(path).texture
        try:
            tex.mag_filter = "nearest"
            tex.min_filter = "nearest"
        except Exception:
            pass
        return tex

    def _label_kwargs(self, font_px):
        kwargs = {"font_size": font_px}
        if self.font_path:
            kwargs["font_name"] = self.font_path
        return kwargs

    def _measure_label(self, text, font_px):
        lbl = CoreLabel(text=text, **self._label_kwargs(font_px))
        lbl.refresh()
        return lbl.texture

    def _draw_label(self, text, x, y, font_px=48, color=(1, 1, 1, 1)):
        tex = self._measure_label(text, font_px)
        self.ui_group.add(Color(*color))
        self.ui_group.add(Rectangle(texture=tex, pos=(x, y), size=tex.size))
        return tex.size

    def _draw_label_custom_group(self, group, text, x, y, font_px=24, color=(1, 1, 1, 1)):
        tex = self._measure_label(text, font_px)
        group.add(Color(*color))
        rect = Rectangle(texture=tex, pos=(x, y), size=tex.size)
        group.add(rect)
        return rect

    def _add_menu_background(self):
        # Dark blue backdrop for menu screens
        self.ui_group.add(Color(0.05, 0.08, 0.2, 1))
        self.ui_group.add(Rectangle(pos=(0, 0), size=(self.width, self.height)))

    def _draw_logo(self, y, max_w=None, max_h=None, scale=1.0):
        logo_path = os.path.join(ASSETS_DIR, "Menu", "project_logo.png")
        if not os.path.exists(logo_path):
            return None
        tex = CoreImage(logo_path).texture
        tex.mag_filter = "nearest"
        tex.min_filter = "nearest"
        w, h = tex.size
        ratio = scale
        if max_w:
            ratio = min(ratio, max_w / w)
        if max_h:
            ratio = min(ratio, max_h / h)
        w *= ratio
        h *= ratio
        x = (self.width - w) / 2
        rect = Rectangle(texture=tex, pos=(x, y), size=(w, h))
        self.ui_group.add(Color(1, 1, 1, 1))
        self.ui_group.add(rect)
        return rect

    def _get_portrait_tex(self, path):
        if not path:
            return None
        if path in self.portrait_cache:
            return self.portrait_cache[path]
        try:
            tex = CoreImage(path).texture
            tex.mag_filter = "nearest"
            tex.min_filter = "nearest"
            self.portrait_cache[path] = tex
            return tex
        except Exception:
            return None

    def _center_label(self, text, y, font_px=48, color=(1, 1, 1, 1)):
        tex = self._measure_label(text, font_px)
        x = (self.width - tex.width) / 2
        self.ui_group.add(Color(*color))
        self.ui_group.add(Rectangle(texture=tex, pos=(x, y), size=tex.size))
        return tex.size

    def _render_main_menu(self):
        self._clear_ui()
        self._add_menu_background()
        logo_scale = 5.0
        logo_max_w = self.width * 0.9
        logo_max_h = self.height * 0.55
        logo_y = self.height * 0.55
        logo_rect = self._draw_logo(logo_y, max_w=logo_max_w, max_h=logo_max_h, scale=logo_scale)
        if logo_rect:
            max_top = self.height * 0.96
            cur_top = logo_rect.pos[1] + logo_rect.size[1]
            if cur_top > max_top:
                shift = cur_top - max_top
                logo_rect.pos = (logo_rect.pos[0], logo_rect.pos[1] - shift)

        btn_w = min(self.width * 0.32, 520)
        btn_h = 120
        btn_x = (self.width - btn_w) / 2
        btn_y = self.height * 0.42
        if logo_rect:
            gap = max(self.height * 0.035, 30)
            btn_y = min(btn_y, logo_rect.pos[1] - btn_h - gap)
        btn_y = max(btn_y, self.height * 0.14)

        self.ui_group.add(Color(0.85, 0.35, 0.25, 1))
        self.ui_group.add(Rectangle(pos=(btn_x, btn_y), size=(btn_w, btn_h)))
        self._main_menu_play_rect = (btn_x, btn_y, btn_w, btn_h)
        # Play label centered in button
        play_tex = self._measure_label("Play", 64)
        lbl_x = btn_x + (btn_w - play_tex.width) / 2
        lbl_y = btn_y + (btn_h - play_tex.height) / 2
        self._draw_label("Play", lbl_x, lbl_y, font_px=64)

        # Control mode selector
        ctrl_w = min(self.width * 0.36, 560)
        ctrl_h = max(90, btn_h * 0.7)
        ctrl_x = (self.width - ctrl_w) / 2
        ctrl_y = btn_y - max(self.height * 0.11, 90)
        self._main_menu_control_rect = (ctrl_x, ctrl_y, ctrl_w, ctrl_h)
        self.ui_group.add(Color(0.15, 0.15, 0.2, 0.8))
        self.ui_group.add(Rectangle(pos=(ctrl_x, ctrl_y), size=(ctrl_w, ctrl_h)))
        mode_label = "Keyboard / Controller" if self.control_mode == "keyboard" else "Touch"
        mode_text = f"Controls: {mode_label}"
        mode_tex = self._measure_label(mode_text, 52)
        mode_x = ctrl_x + (ctrl_w - mode_tex.width) / 2
        mode_y = ctrl_y + (ctrl_h - mode_tex.height) / 2
        self._draw_label(mode_text, mode_x, mode_y, font_px=52)
        hint_text = "Left/Right or tap to switch"
        hint_tex = self._measure_label(hint_text, 32)
        hint_x = ctrl_x + (ctrl_w - hint_tex.width) / 2
        hint_y = ctrl_y - max(28, hint_tex.height + 10)
        self._draw_label(hint_text, hint_x, hint_y, font_px=32, color=(1, 1, 1, 0.7))

        prompt_y = hint_y - max(self.height * 0.05, 42)
        prompt_y = max(prompt_y, self.height * 0.05)
        self._center_label("Press Enter or tap Play to continue", prompt_y, font_px=44, color=(1, 1, 1, 0.8))

    def _render_select_grid(self, title, options, selected_idx):
        self._clear_ui()
        self._add_menu_background()
        self._center_label(title, self.height * 0.72, font_px=96)

        box_size = min(self.width, self.height) * 0.22
        spacing = box_size * 0.1
        start_x = (self.width - (box_size * len(options) + spacing * (len(options) - 1))) / 2
        box_y = self.height * 0.42

        for idx, opt in enumerate(options):
            x = start_x + idx * (box_size + spacing)
            is_selected = idx == selected_idx
            portrait_tex = self._get_portrait_tex(opt.get("portrait"))

            if portrait_tex:
                border = 6
                # Hover border
                if is_selected:
                    self.ui_group.add(Color(0.98, 0.9, 0.1, 1))
                    self.ui_group.add(Rectangle(pos=(x - border, box_y - border), size=(box_size + border * 2, box_size + border * 2)))
                # Portrait
                self.ui_group.add(Color(1, 1, 1, 1))
                tc = portrait_tex.tex_coords
                # Mirror rightmost portrait so they face each other
                if idx == len(options) - 1:
                    tc = (tc[2], tc[3], tc[0], tc[1], tc[6], tc[7], tc[4], tc[5])
                self.ui_group.add(Rectangle(texture=portrait_tex, pos=(x, box_y), size=(box_size, box_size), tex_coords=tc))
                # Name below portrait
                label_tex = self._measure_label(opt["name"], 52)
                lbl_x = x + (box_size - label_tex.width) / 2
                lbl_y = box_y - label_tex.height - 6
                self._draw_label(opt["name"], lbl_x, lbl_y, font_px=52, color=(1, 1, 1, 0.95))
            else:
                base_color = (0.95, 0.65, 0.25, 1) if is_selected else (0.2, 0.2, 0.25, 0.8)
                self.ui_group.add(Color(*base_color))
                self.ui_group.add(Rectangle(pos=(x, box_y), size=(box_size, box_size)))
                # Option label
                label_tex = self._measure_label(opt["name"], 56)
                lbl_x = x + (box_size - label_tex.width) / 2
                lbl_y = box_y + (box_size - label_tex.height) / 2
                self._draw_label(opt["name"], lbl_x, lbl_y, font_px=56, color=(0, 0, 0, 0.9) if is_selected else (1, 1, 1, 0.9))

        self._center_label("Use arrow keys or tap to choose, Enter/tap again to confirm", self.height * 0.22, font_px=44, color=(1, 1, 1, 0.8))

    def _render_character_select(self):
        self._render_select_grid("Choose Your Fighter", self.character_options, self.selected_character_index)

    def _render_stage_select(self):
        self._render_select_grid("Pick a Stage", self.stage_options, self.selected_stage_index)

    def _render_current_ui(self):
        if self.state == "main_menu":
            self._render_main_menu()
        elif self.state == "character_select":
            self._render_character_select()
        elif self.state == "stage_select":
            self._render_stage_select()
        else:
            self._clear_ui()

    # --------------------------------------------------------
    # TOUCH UI
    # --------------------------------------------------------
    def _draw_touch_button(self, x, y, size, label):
        alpha = 0.7
        border_w = max(2.0, size * 0.08)
        self.touch_group.add(Color(0.7, 0.7, 0.7, alpha))
        self.touch_group.add(Rectangle(pos=(x, y), size=(size, size)))
        self.touch_group.add(Color(1, 1, 1, alpha))
        self.touch_group.add(Line(rectangle=(x, y, size, size), width=border_w * 0.35))
        tex = self._measure_label(label, int(size * 0.35))
        lbl_x = x + (size - tex.width) / 2
        lbl_y = y + (size - tex.height) / 2
        self.touch_group.add(Color(1, 1, 1, alpha))
        self.touch_group.add(Rectangle(texture=tex, pos=(lbl_x, lbl_y), size=tex.size))

    def _layout_touch_ui(self):
        self.touch_group.clear()
        self.touch_button_boxes = {}

        if self.control_mode != "touch":
            return
        if self.state in ("main_menu", "character_select", "stage_select"):
            return

        w = float(self.width or Window.size[0] or 1)
        h = float(self.height or Window.size[1] or 1)
        size = min(max(70.0, min(w, h) * 0.09), 140.0)
        pad = w * 0.07
        bottom = h * 0.12
        spacing = size * 1.05

        # D-pad (left side)
        center_x = pad + size * 1.3
        center_y = bottom + size * 1.4
        dpad_positions = {
            "left": (center_x - spacing, center_y),
            "right": (center_x + spacing, center_y),
            "up": (center_x, center_y + spacing),
            "down": (center_x, center_y - spacing),
        }
        for action, (cx, cy) in dpad_positions.items():
            px = cx - size / 2
            py = cy - size / 2
            label = {"left": "\u2190", "right": "\u2192", "up": "\u2191", "down": "\u2193"}[action]
            self._draw_touch_button(px, py, size, label)
            self.touch_button_boxes[action] = (px, py, size, size)

        # Action buttons (right side)
        act_spacing = size * 1.2
        start_x = w - pad - size * 2.6
        act_y = bottom + size * 1.0
        actions = [("punch", "P"), ("kick", "K"), ("special", "S")]
        for idx, (action, label) in enumerate(actions):
            px = start_x + idx * act_spacing
            py = act_y
            self._draw_touch_button(px, py, size, label)
            self.touch_button_boxes[action] = (px, py, size, size)

    def _enter_main_menu(self):
        self.state = "main_menu"
        self._hide_banner()
        self._reset_round_data()
        self._render_main_menu()
        self._layout_touch_ui()

    def _enter_character_select(self):
        self.state = "character_select"
        self._render_character_select()

    def _enter_stage_select(self):
        self.state = "stage_select"
        self._render_stage_select()

    def _move_character_cursor(self, direction):
        total = len(self.character_options)
        self.selected_character_index = (self.selected_character_index + direction) % max(1, total)
        self._render_character_select()

    def _move_stage_cursor(self, direction):
        total = len(self.stage_options)
        self.selected_stage_index = (self.selected_stage_index + direction) % max(1, total)
        self._render_stage_select()

    @property
    def control_mode(self):
        return self.control_modes[self.selected_control_mode_index]

    def _toggle_control_mode(self, delta=1):
        self.selected_control_mode_index = (self.selected_control_mode_index + delta) % max(1, len(self.control_modes))
        if self.state == "main_menu":
            self._render_main_menu()
        self.input.reset()
        self.touch_actions.clear()
        self._pending_jump = False
        self._pending_attack = False
        self._layout_touch_ui()

    def _option_index_from_touch(self, x, options):
        if not options:
            return None
        width = self.width or Window.size[0] or 1
        height = self.height or Window.size[1] or 1
        box_size = min(width, height) * 0.22
        spacing = box_size * 0.1
        start_x = (width - (box_size * len(options) + spacing * (len(options) - 1))) / 2
        centers = [start_x + idx * (box_size + spacing) + box_size / 2 for idx in range(len(options))]
        closest_idx = min(range(len(centers)), key=lambda idx: abs(x - centers[idx]))
        return closest_idx

    def _handle_touch_menu(self, touch):
        if self.state == "main_menu":
            x, y = touch.x, touch.y
            if self._main_menu_play_rect:
                px, py, pw, ph = self._main_menu_play_rect
                if px <= x <= px + pw and py <= y <= py + ph:
                    self._enter_character_select()
                    return True
            if self._main_menu_control_rect:
                cx, cy, cw, ch = self._main_menu_control_rect
                if cx <= x <= cx + cw and cy <= y <= cy + ch:
                    self._toggle_control_mode(1)
                    return True
            # tap elsewhere still starts
            self._enter_character_select()
            return True

        if self.state == "character_select":
            idx = self._option_index_from_touch(touch.x, self.character_options)
            if idx is None:
                return False
            if idx == self.selected_character_index:
                self._enter_stage_select()
            else:
                self.selected_character_index = idx
                self._render_character_select()
            return True

        if self.state == "stage_select":
            idx = self._option_index_from_touch(touch.x, self.stage_options)
            if idx is None:
                return False
            if idx == self.selected_stage_index:
                self._start_match()
            else:
                self.selected_stage_index = idx
                self._render_stage_select()
            return True

        if self.state == "match_over":
            self._reset_match()
            return True

        return False

    # --------------------------------------------------------
    # INPUT HANDLING (P1 ONLY)
    # --------------------------------------------------------
    def _action_from_keyname(self, name):
        if name in ("enter", "space"):
            return "confirm"
        if name in ("left", "a"):
            return "left"
        if name in ("right", "d"):
            return "right"
        if name in ("up", "w"):
            return "up"
        if name in ("down", "s"):
            return "down"
        if name in ("m", "escape", "backspace"):
            return "back"
        return None

    def _handle_menu_action(self, action):
        if self.state == "main_menu":
            if action == "confirm":
                self._enter_character_select()
                return True
            if action in ("left", "right"):
                delta = -1 if action == "left" else 1
                self._toggle_control_mode(delta)
                return True
            return False

        if self.state == "character_select":
            if action in ("left", "up"):
                self._move_character_cursor(-1)
                return True
            if action in ("right", "down"):
                self._move_character_cursor(1)
                return True
            if action == "confirm":
                self._enter_stage_select()
                return True
            return False

        if self.state == "stage_select":
            if action in ("left", "up"):
                self._move_stage_cursor(-1)
                return True
            if action in ("right", "down"):
                self._move_stage_cursor(1)
                return True
            if action == "confirm":
                self._start_match()
                return True
            return False

        if self.state == "match_over":
            if action == "confirm":
                self._reset_match()
                return True
            if action == "back":
                self._enter_main_menu()
                return True
            return False

        return False

    def _queue_jump(self):
        self._pending_jump = True

    def _queue_attack(self):
        self._pending_attack = True

    def _on_key_down(self, window, keycode, scancode, codepoint, modifiers):
        name = keyname_from_event(keycode, codepoint)
        action = self._action_from_keyname(name)

        if action and self._handle_menu_action(action):
            return True

        source = "keyboard"

        if name in ("left", "a"):
            self.input.set("left", True, source)
        elif name in ("right", "d"):
            self.input.set("right", True, source)
        elif name in ("w", "up"):
            if self.input.set("up", True, source):
                self._queue_jump()
        elif name in ("s", "down"):
            self.input.set("down", True, source)
        elif name in ("j", "space"):
            if self.input.set("punch", True, source):
                self._queue_attack()

        return True

    def _on_key_up(self, window, keycode, *args):
        name = keyname_from_keyup(keycode)
        source = "keyboard"

        if name in ("left", "a"):
            self.input.set("left", False, source)
        elif name in ("right", "d"):
            self.input.set("right", False, source)
        elif name in ("w", "up"):
            self.input.set("up", False, source)
        elif name in ("s", "down"):
            self.input.set("down", False, source)
        elif name in ("j", "space"):
            self.input.set("punch", False, source)

        return True

    def _on_joy_axis(self, window, stickid, axisid, value):
        """Map joystick axes to actions. Axis 0: horizontal; Axis 1: vertical (jump)."""
        source = f"pad:{stickid}"
        deadzone = 0.35
        if axisid == 0:
            if value < -deadzone:
                self.input.set("left", True, source)
                self.input.set("right", False, source)
            elif value > deadzone:
                self.input.set("right", True, source)
                self.input.set("left", False, source)
            else:
                self.input.set("left", False, source)
                self.input.set("right", False, source)
        elif axisid == 1:
            if value < -0.55:
                if self.input.set("up", True, source):
                    self._queue_jump()
            else:
                self.input.set("up", False, source)
        return True

    def _on_joy_hat(self, window, stickid, hatid, value):
        source = f"pad:{stickid}:hat{hatid}"
        x, y = value
        self.input.set("left", x < 0, source)
        self.input.set("right", x > 0, source)

        if y > 0:
            if self.input.set("up", True, source):
                self._queue_jump()
        else:
            self.input.set("up", False, source)

        self.input.set("down", y < 0, source)

        # Let the D-pad also steer menus
        if x < 0:
            self._handle_menu_action("left")
        elif x > 0:
            self._handle_menu_action("right")
        elif y > 0:
            self._handle_menu_action("up")
        elif y < 0:
            self._handle_menu_action("down")
        return True

    def _on_joy_button_down(self, window, stickid, buttonid):
        source = f"pad:{stickid}"

        if self.state != "playing" and buttonid in (0, 1, 2, 3, 7):
            if self._handle_menu_action("confirm"):
                return True

        if buttonid in (0, 3):  # A / Y
            if self.input.set("up", True, source):
                self._queue_jump()
        elif buttonid in (1, 2):  # B / X
            if self.input.set("punch", True, source):
                self._queue_attack()
        elif buttonid in (7,):  # Start / Options
            if self._handle_menu_action("confirm"):
                return True

        return True

    def _on_joy_button_up(self, window, stickid, buttonid):
        source = f"pad:{stickid}"

        if buttonid in (0, 3):
            self.input.set("up", False, source)
        elif buttonid in (1, 2):
            self.input.set("punch", False, source)

        return True

    def _actions_from_touch(self, touch):
        """Map touch position to actions using the on-screen buttons."""
        if self.control_mode != "touch":
            return set()
        actions = set()
        hit_pad = max(6.0, min(float(self.width or 0), float(self.height or 0)) * 0.01)
        for action, (x, y, w, h) in self.touch_button_boxes.items():
            if (x - hit_pad) <= touch.x <= (x + w + hit_pad) and (y - hit_pad) <= touch.y <= (y + h + hit_pad):
                actions.add(action)
        return actions

    def _apply_touch_actions(self, touch, actions):
        source = f"touch:{touch.uid}"
        prev_actions = self.touch_actions.get(touch.uid, set())

        # Clear actions that ended
        for action in prev_actions - actions:
            self.input.set(action, False, source)

        # Set new/continued actions
        for action in actions:
            became_active = self.input.set(action, True, source)
            if became_active:
                if action == "up":
                    self._queue_jump()
                elif action in ("punch", "kick"):
                    self._queue_attack()

        if actions:
            self.touch_actions[touch.uid] = actions
        elif touch.uid in self.touch_actions:
            self.touch_actions.pop(touch.uid, None)

    def on_touch_down(self, touch):
        # Menu taps: treat as confirm/select
        if self.state in ("main_menu", "character_select", "stage_select", "match_over"):
            if self._handle_touch_menu(touch):
                return True

        if self.control_mode != "touch":
            return super().on_touch_down(touch)
        if self.state not in ("playing", "round_over", "match_over"):
            return super().on_touch_down(touch)

        actions = self._actions_from_touch(touch)
        if not actions:
            return super().on_touch_down(touch)
        self._apply_touch_actions(touch, actions)
        return True

    def on_touch_move(self, touch):
        if self.control_mode != "touch":
            return super().on_touch_move(touch)
        if self.state not in ("playing", "round_over", "match_over"):
            return super().on_touch_move(touch)

        actions = self._actions_from_touch(touch)
        if not actions and touch.uid not in self.touch_actions:
            return super().on_touch_move(touch)
        self._apply_touch_actions(touch, actions)
        return True

    def on_touch_up(self, touch):
        if self.control_mode != "touch":
            return super().on_touch_up(touch)
        source = f"touch:{touch.uid}"
        self.input.clear_source(source)
        self.touch_actions.pop(touch.uid, None)
        return True

    def _apply_input_p1(self, dt):
        if self._pending_jump:
            self.p1.jump()
            self._pending_jump = False
        if self._pending_attack:
            self.p1.start_attack()
            self._pending_attack = False

        left = self.input.get("left")
        right = self.input.get("right")

        if left and not right:
            self.p1.move_left()
        elif right and not left:
            self.p1.move_right()
        else:
            self.p1.stop()

    # --------------------------------------------------------
    # ENEMY AI (simple starter)
    # --------------------------------------------------------
    def _ai_update(self, dt):
        if self.state != "playing":
            return

        p1 = self.p1
        p2 = self.p2

        distance = abs(p1.x - p2.x)
        horiz_dir = 1 if p1.x > p2.x else -1

        # Determine facing
        p2.facing = 1 if p2.x < p1.x else -1

        # --- AI PARAMETERS / ranges ---
        CLOSE_RANGE = 130
        SWEET_RANGE = 200
        FAR_RANGE = 320
        JUMP_TRIGGER_DIST = 260
        THINK_BASE = 0.14

        # Short-circuit anti-air: if player is airborne near us, swat
        if p1.y - p1.floor_y > 70 and distance < SWEET_RANGE:
            if random.random() < 0.95:
                p2.start_attack()
                self._ai_timer = 0.12
                return

        # React to active attacks by backing up briefly
        if p1.attack and p1.attack["phase"] in ("startup", "active") and distance < SWEET_RANGE:
            self._ai_action = {"type": "retreat", "time": 0.35, "dir": -horiz_dir}

        # Continue any in-progress action to reduce jitter
        if self._ai_action and self._ai_action["time"] > 0:
            act = self._ai_action
            act["time"] -= dt
            if act["type"] == "retreat":
                if act["dir"] < 0:
                    p2.move_left()
                else:
                    p2.move_right()
            elif act["type"] == "approach":
                if horiz_dir > 0:
                    p2.move_right()
                else:
                    p2.move_left()
            elif act["type"] == "wait":
                p2.stop()
            elif act["type"] == "jump_in":
                # one jump impulse then keep moving forward
                if not act.get("did_jump"):
                    p2.jump()
                    act["did_jump"] = True
                if horiz_dir > 0:
                    p2.move_right()
                else:
                    p2.move_left()
            elif act["type"] == "advance_poke":
                if act.get("dir", horiz_dir) > 0:
                    p2.move_right()
                else:
                    p2.move_left()
                if not act.get("did_attack") and act["time"] < 0.2:
                    p2.start_attack()
                    act["did_attack"] = True
            # If still time left, don't re-think yet
            if act["time"] > 0:
                return
            self._ai_action = None

        # throttle decisions
        self._ai_timer = max(0, self._ai_timer - dt)
        if self._ai_timer > 0:
            return

        # Decision cadence adapts slightly by range
        if distance < CLOSE_RANGE:
            self._ai_timer = THINK_BASE * 0.55
        elif distance < SWEET_RANGE:
            self._ai_timer = THINK_BASE * 0.9
        else:
            self._ai_timer = THINK_BASE * 1.1

        # -----------------------------
        # Distance-based behavior
        # -----------------------------
        if distance > FAR_RANGE:
            # Too far: approach, occasionally jump in
            if random.random() < 0.3 and distance > JUMP_TRIGGER_DIST:
                self._ai_action = {"type": "jump_in", "time": 0.6}
                return
            if random.random() < 0.5:
                self._ai_action = {"type": "advance_poke", "time": 0.55, "dir": horiz_dir}
            else:
                self._ai_action = {"type": "approach", "time": 0.45}
            return

        if distance > SWEET_RANGE:
            # Mid-far footsie walk forward with a chance to pause
            roll = random.random()
            if roll < 0.15:
                self._ai_action = {"type": "wait", "time": 0.14}
            elif roll < 0.5:
                self._ai_action = {"type": "advance_poke", "time": 0.4, "dir": horiz_dir}
            else:
                self._ai_action = {"type": "approach", "time": 0.3}
            return

        if distance < CLOSE_RANGE:
            # Too close: either jab or back off
            if random.random() < 0.9:
                p2.start_attack()
                self._ai_timer = 0.16
            else:
                self._ai_action = {"type": "retreat", "time": 0.2, "dir": -horiz_dir}
            return

        # Sweet spot: poke or shimmy
        roll = random.random()
        if roll < 0.7:
            p2.start_attack()
            self._ai_timer = 0.18
        elif roll < 0.82:
            self._ai_action = {"type": "advance_poke", "time": 0.22, "dir": horiz_dir}
        elif roll < 0.94:
            self._ai_action = {"type": "retreat", "time": 0.16, "dir": -horiz_dir}
        else:
            self._ai_action = {"type": "wait", "time": 0.1}

    # --------------------------------------------------------
    # HIT DETECTION
    # --------------------------------------------------------
    @staticmethod
    def aabb(a, b):
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        return not (ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay)

    def _check_hit(self, attacker, defender):
        if not attacker.attack:
            return

        hitbox = attacker.attack_hitbox()
        if not hitbox:
            return

        hurtbox = defender.hurtbox()

        if attacker.attack["phase"] == "active" and not attacker.attack["has_hit"] and self.aabb(hitbox, hurtbox):
            attacker.attack["has_hit"] = True
            defender.hp = max(0, defender.hp - attacker.attack_cfg["dmg"])
            self._update_health_bars()

            # -------------------------
            # Knockback effect!
            # -------------------------
            # Direction: push defender away from attacker
            direction = 1 if defender.x > attacker.x else -1
            defender.defeat_knock_dir = direction

            # Stronger knockback for more impact
            defender.knockback_vx = direction * 620 * PHYSICS_SCALE  # increased knockback scaled to sprite size

            # Apply hitstun
            defender.hitstun = 0.24  # slight increase for more pronounced pause
            defender.on_hit()

            self._update_health_bars()

            if defender.hp <= 0:
                # Extra knockback on defeat
                defender.knockback_vx = direction * 1800 * PHYSICS_SCALE
                defender.on_defeat()
                attacker.on_victory()
                self._end_round("P1" if defender is self.p2 else "P2")

    # --------------------------------------------------------
    # ROUND / MATCH SYSTEM
    # --------------------------------------------------------
    def _show_banner(self, text, seconds=None, font_px=72):
        # Clear previous banner
        self.banner_group.clear()

        # Render text
        lbl = CoreLabel(text=text, **self._label_kwargs(font_px))
        lbl.refresh()
        tex = lbl.texture

        x = (self.width - tex.width) / 2
        y = (self.height - tex.height) / 2

        # Create instructions manually (InstructionGroup does NOT support "with")
        color = Color(1, 1, 1, 1)
        rect = Rectangle(texture=tex, pos=(x, y), size=tex.size)

        # Store for reference
        self.banner = rect

        # Add to banner_group
        self.banner_group.add(color)
        self.banner_group.add(rect)

        # Auto-hide
        if seconds:
            Clock.schedule_once(lambda *_: self._hide_banner(), seconds)

    def _hide_banner(self, *args):
        self.banner_group.clear()
        self.banner = None

    def _show_fight_overlay(self, duration=2.0):
        """Display the 'Fight' asset centered on screen for the given duration."""
        fight_path = os.path.join(ASSETS_DIR, "Menu", "Fight.png")
        self.banner_group.clear()
        if os.path.exists(fight_path):
            tex = CoreImage(fight_path).texture
            try:
                tex.mag_filter = "nearest"
                tex.min_filter = "nearest"
            except Exception:
                pass
            w, h = tex.size
            max_w = self.width * 0.99
            max_h = self.height * 0.99
            # Allow up to 5x upscale so the word really fills the screen
            ratio = min(max_w / max(1, w), max_h / max(1, h), 10.0)
            w *= ratio
            h *= ratio
            x = (self.width - w) / 2
            y = (self.height - h) / 2
            self.banner_group.add(Color(1, 1, 1, 1))
            self.banner_group.add(Rectangle(texture=tex, pos=(x, y), size=(w, h)))
        else:
            # Fallback to text if asset missing
            self._show_banner("FIGHT!", seconds=None, font_px=96)
        if duration:
            Clock.schedule_once(lambda *_: self._hide_banner(), duration)

    def _reset_round_data(self):
        p1_x, p2_x = self._start_positions()
        self.p1.floor_y = self.floor_y
        self.p2.floor_y = self.floor_y
        self.p1.stage_width = self.stage_width
        self.p2.stage_width = self.stage_width
        self.p1.x, self.p1.y = p1_x, self.floor_y
        self.p1.vx = self.p1.vy = 0
        self.p1.hp = 100
        self.p1.defeated = False
        self.p1.victorious = False
        self.p1.defeat_impact_count = 0
        self.p1.defeat_landing_event = None
        self.p1.defeat_knock_dir = 1

        self.p2.x, self.p2.y = p2_x, self.floor_y
        self.p2.vx = self.p2.vy = 0
        self.p2.hp = 100
        self.p2.defeated = False
        self.p2.victorious = False
        self.p2.defeat_impact_count = 0
        self.p2.defeat_landing_event = None
        self.p2.defeat_knock_dir = -1

        self.p1.attack = None
        self.p2.attack = None
        self.fx.clear()
        self.round_timer = 60
        self._timer_accum = 0.0
        self._update_health_bars()
        self._render_timer()
        self._render_round_counters()
        self._sync_draw()

    def _end_round(self, winner):
        self.state = "round_over"
        if winner == "P1":
            self.p1_wins += 1
        else:
            self.p2_wins += 1

        self._render_round_counters()

        pause = 5.0
        self._show_banner(f"{winner} WINS!", seconds=pause)

        if self.p1_wins >= self.max_wins or self.p2_wins >= self.max_wins:
            Clock.schedule_once(lambda *_: self._end_match(), pause + 0.1)
        else:
            Clock.schedule_once(lambda *_: self._start_next_round(), pause + 0.1)

    def _start_next_round(self):
        self.round += 1
        self._reset_round_data()
        self._queue_round_intro(self.round)
        self._layout_touch_ui()

    def _resume_play(self, hide_banner=True):
        if hide_banner:
            self._hide_banner()
        self.state = "playing"
        self._layout_touch_ui()

    def _end_match(self):
        txt = "VICTORY!" if self.p1_wins > self.p2_wins else "DEFEAT..."
        self._show_banner(f"{txt}\n\nPress R or tap to restart", seconds=None)
        self.state = "match_over"
        self._layout_touch_ui()

    def _reset_match(self):
        self._start_match()

    def _apply_selection(self):
        player_choice = self.character_options[self.selected_character_index]
        if len(self.character_options) > 1:
            opp_idx = (self.selected_character_index + 1) % len(self.character_options)
        else:
            opp_idx = 0
        opponent_choice = self.character_options[opp_idx]

        self.p1.reload_sprites(player_choice["loader"]())
        self.p2.reload_sprites(opponent_choice["loader"]())
        stage_choice = self.stage_options[self.selected_stage_index]
        self.current_stage_key = stage_choice["key"]
        self._load_stage(self.current_stage_key)
        self.p1.floor_y = self.floor_y
        self.p2.floor_y = self.floor_y
        self.p1_name = player_choice["name"]
        self.p2_name = opponent_choice["name"]
        Window.title = f"2D Fighter — {stage_choice['name']}"

    def _start_match(self):
        self._clear_ui()
        self.input.reset()
        self.touch_actions.clear()
        self._pending_jump = False
        self._pending_attack = False
        self._apply_selection()
        self._build_scene()
        self.state = "round_over"  # temporary gate to block input until intro ends
        self.round = 1
        self.p1_wins = 0
        self.p2_wins = 0
        self._reset_round_data()
        stage_name = self.stage_options[self.selected_stage_index]["name"]
        self._queue_round_intro(self.round, stage_name=stage_name)
        self._layout_touch_ui()

    def _handle_defeat_impacts(self):
        for fighter in (self.p1, self.p2):
            event = getattr(fighter, "defeat_landing_event", None)
            if not event:
                continue
            if event == "first":
                self._trigger_shake(strength=18, duration=0.28)
            else:
                self._trigger_shake(strength=24, duration=0.36)

    def _queue_round_intro(self, round_number, stage_name=None):
        """Show round banner for 3s, then 'Fight' overlay for 2s; gameplay starts at 3s."""
        intro_time = 3.0
        fight_time = 2.0
        lines = [f"ROUND {round_number}"]
        if stage_name:
            lines.append(stage_name)
        self._show_banner("\n".join(lines), seconds=None)
        # Start gameplay and show fight overlay after intro_time
        Clock.schedule_once(lambda *_: self._show_fight_overlay(duration=fight_time), intro_time)
        Clock.schedule_once(lambda *_: self._resume_play(hide_banner=False), intro_time)

    # --------------------------------------------------------
    # MAIN UPDATE LOOP
    # --------------------------------------------------------
    def update(self, dt):
        if self.state != "playing":
            self.p1.update(dt, self.gravity)
            self.p2.update(dt, self.gravity)
            self._handle_defeat_impacts()
            self._update_shake(dt)
            self._layout_bg_cover()
            self._sync_draw()
            return

        # Player input
        self._apply_input_p1(dt)

        # Enemy AI
        self._ai_update(dt)

        # Round timer
        self._timer_accum += dt
        if self._timer_accum >= 1.0 and self.round_timer > 0:
            ticks = int(self._timer_accum)
            self._timer_accum -= ticks
            self.round_timer = max(0, self.round_timer - ticks)
            self._render_timer()

        # Update fighters
        self.p1.update(dt, self.gravity)
        self.p2.update(dt, self.gravity)

        # Keep fighters from overlapping
        self._separate_fighters()

        # Hit detection both ways
        self._check_hit(self.p1, self.p2)
        self._check_hit(self.p2, self.p1)

        self._handle_defeat_impacts()
        self._update_shake(dt)
        self._draw_debug_boxes()
        self._layout_bg_cover()
        self._sync_draw()

    def _start_positions(self):
        """Place fighters at ~15% and ~85% of the screen width."""
        from game_fighter.constants import STAGE_MARGIN

        win_w = self.stage_width
        scale_ratio = self._compute_sprite_scale() / float(SPRITE_SCALE)
        eff_size = SPRITE_SIZE * scale_ratio
        left = max(STAGE_MARGIN, win_w * 0.15 - eff_size * 0.5)
        right = min(win_w - eff_size - STAGE_MARGIN, win_w * 0.85 - eff_size * 0.5)
        return left, right

    def _separate_fighters(self):
        """Prevent fighters from occupying the same space by pushing them apart horizontally."""
        x1, y1, w1, h1 = self.p1.hurtbox()
        x2, y2, w2, h2 = self.p2.hurtbox()

        # Only resolve if their hurtboxes overlap vertically (likely always on ground)
        vertical_overlap = not (y1 + h1 <= y2 or y2 + h2 <= y1)
        if not vertical_overlap:
            return

        overlap_x = min(x1 + w1, x2 + w2) - max(x1, x2)
        if overlap_x <= 0:
            return

        push = overlap_x / 2.0 + 1.0  # small bias prevents re-overlap next frame
        if x1 <= x2:
            self.p1.x -= push
            self.p2.x += push
        else:
            self.p1.x += push
            self.p2.x -= push

        from game_fighter.constants import STAGE_MARGIN
        max_x = self.stage_width - SPRITE_SIZE - STAGE_MARGIN
        self.p1.x = max(STAGE_MARGIN, min(max_x, self.p1.x))
        self.p2.x = max(STAGE_MARGIN, min(max_x, self.p2.x))

    # --------------------------------------------------------
    # CAMERA
    # --------------------------------------------------------
    def _trigger_shake(self, strength=14, duration=0.32):
        """Start a brief camera shake with the given strength/duration."""
        self.shake_strength = max(self.shake_strength, strength)
        self.shake_time = max(self.shake_time, duration)
        self.shake_duration = max(self.shake_duration, duration)

    def _update_shake(self, dt):
        if self.shake_time <= 0:
            self.shake_offset = (0.0, 0.0)
            return
        self.shake_time = max(0.0, self.shake_time - dt)
        if self.shake_duration <= 0:
            self.shake_offset = (0.0, 0.0)
            return
        t = self.shake_time / self.shake_duration
        magnitude = self.shake_strength * (t * t)
        self.shake_offset = (
            random.uniform(-1.0, 1.0) * magnitude,
            random.uniform(-1.0, 1.0) * magnitude,
        )
        if self.shake_time <= 0:
            self.shake_strength = 0.0
            self.shake_duration = 0.0
            self.shake_offset = (0.0, 0.0)

    def _update_camera(self):
        if not self.transform_before or not self.transform_after:
            return
        self.transform_before.clear()
        self.transform_after.clear()

        # Visible width/height at current zoom
        scale = max(1.0, self.camera_scale)
        vis_w = (self.width or 1) / scale
        vis_h = (self.height or 1) / scale

        center_x = (self.p1.x + self.p2.x) / 2.0
        target_x = center_x - vis_w / 2.0
        target_x = max(0, min(max(0, self.stage_width - vis_w), target_x))
        target_y = 0  # keep floor at bottom

        # Smooth toward target
        smooth = self.camera_smooth
        self.cam_x = self.cam_x * (1 - smooth) + target_x * smooth
        self.cam_y = self.cam_y * (1 - smooth) + target_y * smooth

        self.transform_before.add(PushMatrix())
        self.transform_before.add(Scale(scale, scale, 1))
        sx, sy = self.shake_offset
        self.transform_before.add(Translate(-(self.cam_x + sx), -(self.cam_y + sy), 0))
        self.transform_after.add(PopMatrix())
