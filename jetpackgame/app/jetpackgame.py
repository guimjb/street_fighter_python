#!/usr/bin/env python3
from pathlib import Path

from kivy.core.audio import SoundLoader
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, BooleanProperty, StringProperty
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.graphics import Color, Rectangle, Line, Triangle, PushMatrix, PopMatrix, Rotate
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.resources import resource_find, resource_add_path
from kivy.metrics import sp
from kivy.animation import Animation
from kivy.core.window import Window
import random, math

APP_DIR = Path(__file__).resolve().parent
resource_add_path(str(APP_DIR))
Builder.load_file(str(APP_DIR / "main.kv"))

high_score_responses = [
    {"text": "Wow! That's a high score!", "sound": "assets/hiscore.mp3", "portrait": "assets/char2.png"},
    {"text": "You just hit a new record.", "sound": "assets/nrecord.mp3", "portrait": "assets/char1.png"},
    {"text": "You're doing great, dude.", "sound": "assets/great.mp3", "portrait": "assets/char1.png"},
    {"text": "You're on fire! Keep it up!", "sound": "assets/fire.mp3", "portrait": "assets/char2.png"},
    {"text": "I'm impressed, Buttons.", "sound": "assets/impress.mp3", "portrait": "assets/char1.png"}
]

def get_random_response():
    return random.choice(high_score_responses)


# --- Core Widgets ---
class FarBackground(Widget):
    source = StringProperty("assets/background_far.png")

class Background(Widget):
    source = StringProperty("assets/background.png")

class Player(Image):
    state = StringProperty("run1")
    frame_timer = NumericProperty(0)
    velocity_y = NumericProperty(0)  # positive = up, negative = down
    width_ratio = NumericProperty(0.08)
    height_ratio = NumericProperty(0.08)

    collision_padding_x = NumericProperty(0.25)
    collision_padding_y = NumericProperty(0.25)

    on_ground = BooleanProperty(True)  # can still be used if needed

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source = "assets/player_run1.png"
        self.size_hint = (None, None)
        self.allow_stretch = True
        self.keep_ratio = True

        # Initial size
        self.update_size(Window.width, Window.height)
        Window.bind(on_resize=self.on_window_resize)

    def update_size(self, screen_width, screen_height):
        self.width = screen_width * self.width_ratio
        self.height = screen_height * self.height_ratio

    def on_window_resize(self, window, width, height):
        self.update_size(width, height)

    def check_grounded(self, ground_y):
        """Optional: update on_ground based on y-position."""
        self.on_ground = self.y <= ground_y
        if self.on_ground:
            self.y = ground_y

    def get_hitbox(self):
        """Return the hitbox (always grounded size)."""
        pad_x = self.width * self.collision_padding_x
        pad_y = self.height * self.collision_padding_y
        return (self.x + pad_x, self.y + pad_y,
                self.width - 2 * pad_x, self.height - 2 * pad_y)

class DialogueBox(BoxLayout):
    def __init__(self, text, portrait, screen_width, screen_height, **kwargs):
        super().__init__(orientation='horizontal',
                         size_hint=(None, None),
                         width=screen_width * 0.8,
                         height=screen_height * 0.15,
                         padding=screen_width*0.02,
                         spacing=screen_width*0.02,
                         opacity=0,  # start invisible
                         **kwargs)
        
        # Character portrait
        self.add_widget(Image(source=portrait,
                              size_hint=(None, 1),
                              width=screen_width * 0.15))
        
        # Dialogue text
        self.add_widget(Label(text=text,
                              halign='left',
                              valign='middle',
                              text_size=(screen_width*0.6, None)))

        # Start fade in animation
        self.fade_in()

    def fade_in(self, duration=0.2):
        Animation(opacity=1, duration=duration).start(self)

    def fade_out(self, duration=0.2, on_complete=None):
        anim = Animation(opacity=0, duration=duration)
        if on_complete:
            anim.bind(on_complete=lambda *args: on_complete())
        anim.start(self)


class Coin(Image):
    def __init__(self, screen_width, screen_height, scroll_speed=300, period=3.0, **kwargs):
        super().__init__(**kwargs)
        self.source = "assets/coin.png"
        self.size_hint = (None, None)
        self.width = screen_width * 0.06
        self.height = screen_width * 0.06
        self.scroll_speed = scroll_speed
        self.period = period
        self.time = 0
        self.collected = False
        self.min_y = screen_height * 0.3
        self.max_y = screen_height * 0.95
        self.base_y = (self.min_y + self.max_y) / 2
        self.amplitude = (self.max_y - self.min_y) / 2 - self.height / 2
        self.x = screen_width
        self.y = self.base_y

    def move(self, dt):
        self.time += dt
        self.x -= self.scroll_speed * dt
        wave = math.sin(2 * math.pi * (self.time / self.period))
        self.y = self.base_y + self.amplitude * wave
        self.y += math.sin(4 * math.pi * (self.time / self.period)) * (self.amplitude * 0.05)
        return not self.collected and self.right > 0
        
    def get_hitbox(self):
        return (self.x, self.y, self.width, self.height)
        
class Obstacle(Widget):
    obstacle_type = StringProperty("vertical")
    angle = NumericProperty(0)

    def collides_with(self, player):
        # Always use player's padded custom hitbox, not image size
        px, py, pw, ph = player.get_hitbox()

        # AABB collision
        return (px < self.right and px + pw > self.x and
                py < self.top and py + ph > self.y)

class Crosshair(Widget):
    active = BooleanProperty(True)
    flash_state = BooleanProperty(True)
    flash_timer = 0
    tracking = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self.color = Color(1, 0, 0, 1)
            self.line1 = Line(points=[], width=3)
            self.line2 = Line(points=[], width=3)
        Clock.schedule_interval(self.update_crosshair, 1/30)

    def update_crosshair(self, dt):
        if not self.active:
            return
        self.flash_timer += dt
        if self.flash_timer >= 0.15:
            self.flash_state = not self.flash_state
            self.flash_timer = 0
        self.color.a = 1 if self.flash_state else 0.3
        size = min(self.width, self.height) / 2
        x1, y1 = self.center_x - size, self.center_y - size
        x2, y2 = self.center_x + size, self.center_y + size
        x3, y3 = self.center_x - size, self.center_y + size
        x4, y4 = self.center_x + size, self.center_y - size
        self.line1.points = [x1, y1, x2, y2]
        self.line2.points = [x3, y3, x4, y4]

class Missile(Widget):
    base_velocity_x = NumericProperty(-12)
    max_velocity_x = NumericProperty(-28)

    def move(self, dt, difficulty_multiplier=1.0):
        scaled_velocity = max(self.base_velocity_x * difficulty_multiplier, self.max_velocity_x)
        self.x += scaled_velocity * dt * 60
        return self.right > 0
        
    def get_hitbox(self):
        return (self.x, self.y, self.width, self.height)

# --- Screens ---
class StartScreen(Screen):
    high_score = NumericProperty(0)
    pass
    
class GameOverScreen(Screen):
    final_score = NumericProperty(0)
    high_score = NumericProperty(0)
    new_high_score = BooleanProperty(False)

class GameScreen(Screen):
    score = NumericProperty(0)
    hit_pause = BooleanProperty(False)
    game_over_triggered = BooleanProperty(False)
    high_score = NumericProperty(0)
    new_high_score = BooleanProperty(False)
    high_score_event_triggered = BooleanProperty(False)

    # Coin settings
    COIN_INTERVAL = 10.0          # seconds between potential spawns
    COIN_SPAWN_CHANCE = 0.67      # spawn chance
    _coin_timer = 0.0             # internal timer for coin spawning

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # --- Game state ---
        self.coins = []  # active coins in the game
        self._coin_timer = 0.0
        self._time_accumulator = 0.0
        self._obstacle_timer = 0.0
        self._tracking_missile_timer = 0.0
        self._nontracking_missile_timer = 0.0
        self.thrusting = False
        self.difficulty_multiplier = 1.0

        # Hit pause / game over flags
        self.game_over_triggered = False
        self.hit_pause = False
        self._hit_pause_scheduled = False
        self._hit_pause_event = None
        self._suppress_scheduled_actions = False

        # Sound attributes
        self.bg_music = None
        self.crosshair_sounds = []
        self.missile_sounds = []

        # Intro
        self.intro_playing = True

        # Initialize other lists
        self.obstacles = []
        self.crosshairs = []
        self.missiles = []

        # Load sounds
        self.load_sounds()

    _time_accumulator = 0
    thrusting = BooleanProperty(False)
    obstacles = []
    crosshairs = []
    missiles = []

    GRAVITY = 0.4
    THRUST = 1.1
    MAX_UPWARD_SPEED = 12

    OBSTACLE_INTERVAL = 2.0
    SKIP_CHANCE = 0.1

    TRACKING_MISSILE_INTERVAL = 10
    NONTRACKING_MISSILE_INTERVAL = 4

    BASE_SCROLL_SPEED = 5
    MAX_SCROLL_SPEED = 20
    DIFFICULTY_RISE_RATE = 0.03

    BRIDGE_HEIGHT_RATIO = 0.30

    PLAYER_WIDTH_RATIO = 0.06
    PLAYER_HEIGHT_RATIO = 0.08

    OBSTACLE_WIDTH_RATIO = 0.03
    OBSTACLE_HEIGHT_MIN_RATIO = 0.175
    OBSTACLE_HEIGHT_MAX_RATIO = 0.275

    CROSSHAIR_SIZE_RATIO = 0.03
    MISSILE_WIDTH_RATIO = 0.07
    MISSILE_HEIGHT_RATIO = 0.05

    hit_pause = BooleanProperty(False)
    HIT_PAUSE_DURATION = 1.0  # seconds

    game_over_triggered = BooleanProperty(False)

    # Internal helper flags/events
    _hit_pause_scheduled = False
    _hit_pause_event = None
    _fade_event_holder = {"e": None}
    _suppress_scheduled_actions = False

    # --- Lifecycle ---
    def on_enter(self):
        self.reset_game()
        player = self.ids.player
        player.width_ratio = 0.15
        player.height_ratio = 0.15
        player.update_size(Window.width, Window.height)
        self.intro_playing = True  # start intro
        self.player_intro()        # run intro animation
        self._clock = Clock.schedule_interval(self.update, 1/60)
        self.hit_pause = False
        self.game_over_triggered = False
        self._hit_pause_scheduled = False
        self._hit_pause_event = None
        self._fade_event_holder = {"e": None}

        # play music only if not already playing
        if self.bg_music and self.bg_music.state != "play":
            self.bg_music.play()

    # Intro
    def player_intro(self):
        player = self.ids.player
        target_x = self.width * 0.2  # desired starting x position
        speed = 600  # smooth intro speed in pixels/sec

        # Cancel previous intro if any
        if hasattr(self, "_intro_event") and self._intro_event:
            try:
                self._intro_event.cancel()
            except Exception:
                pass

        def move_player(dt):
            distance = speed * dt
            if player.x + distance < target_x:
                player.x += distance
            else:
                player.x = target_x
                self.intro_playing = False
                self._intro_event = None
                return False  # stop Clock

        self._intro_event = Clock.schedule_interval(move_player, 1/60)

    def update_player_sprite(self, dt):
        p = self.ids.player
        ground_y = self.BRIDGE_HEIGHT

        # --- Flying ---
        if self.thrusting:
            p.state = "fly"
            p.source = "assets/player_fly.png"
            return

        # --- Falling ---
        if p.y > ground_y + 1:  # slightly above ground
            p.state = "fall"
            p.source = "assets/player_fall.png"
            return

        # --- Running on ground ---
        if p.y <= ground_y + 1:  # slightly above bridge
            p.frame_timer += dt
            if p.frame_timer >= 0.15:  # swap every 0.15 sec
                if p.state in ["run1", "run2", "fall", "fly"]:
                    # toggle between run1/run2
                    p.state = "run2" if p.state == "run1" else "run1"
                p.source = f"assets/player_{p.state}.png"
                p.frame_timer = 0

    # --- GameScreen lifecycle ---
    def on_leave(self):
        if hasattr(self, "_clock") and self._clock:
            self._clock.cancel()

        # cancel any pending fade events
        if self._fade_event_holder.get("e"):
            try:
                self._fade_event_holder["e"].cancel()
            except Exception:
                pass
            self._fade_event_holder["e"] = None

        if self.bg_music:
            self.bg_music.stop()

    # --- Sounds ---
    def load_sounds(self):
        def safe_load(path):
            try:
                s = SoundLoader.load(path)
                return s
            except Exception:
                return None

        # Background music
        if self.bg_music is None:  # only load once
            self.bg_music = safe_load("assets/backgroundmusic.mp3")
            if self.bg_music:
                self.bg_music.loop = True
                self.bg_music.volume = 0.5

        # Crosshair sounds
        if not self.crosshair_sounds:
            self.crosshair_sounds = [safe_load("assets/crosshair_beep.mp3") for _ in range(5)]

        # Missile sounds
        if not self.missile_sounds:
            self.missile_sounds = [safe_load("assets/missile_fire.mp3") for _ in range(5)]

        # --- Preload high score sounds ---
        for response in high_score_responses:
            if response["sound"] and response.get("sound_obj") is None:
                response["sound_obj"] = safe_load(response["sound"])

    # --- Reset ---
    def reset_game(self):
        self.score = 0
        self._time_accumulator = 0
        self._obstacle_timer = 0
        self._tracking_missile_timer = 0
        self._nontracking_missile_timer = 0
        self.thrusting = False
        self.difficulty_multiplier = 1.0
        self.game_over_triggered = False
        self._hit_pause_scheduled = False
        self.hit_pause = False
        self._hit_pause_event = None
        self._suppress_scheduled_actions = False
        self._coin_timer = 0.0
        self._high_score_event_triggered = False

        # dynamic sizing & player reset
        player = self.ids.player
        player.width = self.width * self.PLAYER_WIDTH_RATIO
        player.height = self.height * self.PLAYER_HEIGHT_RATIO
        self.BRIDGE_HEIGHT = self.height * self.BRIDGE_HEIGHT_RATIO

        # Place player off-screen left
        player.x = -player.width
        player.y = self.BRIDGE_HEIGHT
        player.velocity_y = 0

        # backgrounds
        for bg in [self.ids.bg1, self.ids.bg2, self.ids.bg_far1, self.ids.bg_far2]:
            bg.width = self.width
            bg.height = self.height
        self.ids.bg1.x = 0
        self.ids.bg2.x = self.width
        self.ids.bg_far1.x = 0
        self.ids.bg_far2.x = self.width

        # clear old objects
        for lst in [self.obstacles, self.crosshairs, self.missiles]:
            for obj in lst:
                try:
                    self.ids.obstacles_layout.remove_widget(obj)
                except Exception:
                    pass
            lst.clear()

        # --- clear coins ---
        for coin in list(self.coins):
            try:
                self.ids.obstacles_layout.remove_widget(coin)
            except Exception:
                pass
        self.coins.clear()

        # --- reset music volume if it exists, but don't play ---
        if hasattr(self, "bg_music") and self.bg_music:
            try:
                self.bg_music.stop()  # just reset in case it was playing
                self.bg_music.volume = 0.5
            except Exception:
                pass

    def play_sound(self, sound_list):
        for s in sound_list:
            if s and getattr(s, "state", None) != "play":
                try:
                    s.stop()
                    s.play()
                except Exception:
                    pass
                break

    # --- Update loop ---
    def update(self, dt):
        self.update_player_sprite(dt)  # always update sprite
        # If game over triggered OR during hit pause, skip updating gameplay.
        if self.game_over_triggered or self.hit_pause or getattr(self, "intro_playing", False):
            return
        
        dt = min(dt, 1/30)
        self.difficulty_multiplier += self.DIFFICULTY_RISE_RATE * dt
        scroll_speed = min(self.BASE_SCROLL_SPEED * self.difficulty_multiplier, self.MAX_SCROLL_SPEED)

        # Background parallax
        for name, pair in {"near": (self.ids.bg1, self.ids.bg2),
                           "far": (self.ids.bg_far1, self.ids.bg_far2)}.items():
            speed = scroll_speed * (0.5 if "far" in name else 1)
            for bg in pair:
                bg.x -= speed
                if bg.right <= 0:
                    bg.x += self.width * 2

        # --- Player movement (gradual thrust restored) ---
        player = self.ids.player
        if self.thrusting:
            # apply thrust gradually
            player.velocity_y += self.THRUST * dt * 60
            if player.velocity_y > self.MAX_UPWARD_SPEED:
                player.velocity_y = self.MAX_UPWARD_SPEED
        # gravity always applies every frame
        player.velocity_y -= self.GRAVITY * dt * 60
        player.y += player.velocity_y * dt * 60

        # Clamp bottom (bridge)
        if player.y <= self.BRIDGE_HEIGHT:
            player.y = self.BRIDGE_HEIGHT
            if player.velocity_y < 0:
                player.velocity_y = 0

        # Clamp top
        if player.y + player.height >= self.height:
            player.y = self.height - player.height
            if player.velocity_y > 0:
                player.velocity_y = 0

        # --- Scoring ---
        self._time_accumulator += dt
        if self._time_accumulator >= 0.2:
            self.score += 1
            self._time_accumulator = 0

        # --- Spawn obstacles & crosshairs ---
        self._obstacle_timer += dt
        if self._obstacle_timer >= self.OBSTACLE_INTERVAL:
            self.spawn_obstacle()
            self._obstacle_timer = 0

        self._tracking_missile_timer += dt
        if self._tracking_missile_timer >= self.TRACKING_MISSILE_INTERVAL:
            self.spawn_crosshair(tracking=True)
            self._tracking_missile_timer = 0

        self._nontracking_missile_timer += dt
        if self._nontracking_missile_timer >= self.NONTRACKING_MISSILE_INTERVAL:
            self.spawn_crosshair(tracking=False)
            self._nontracking_missile_timer = 0

        # --- Move obstacles and check collision ---
        for obs in list(self.obstacles):
            obs.x -= scroll_speed

            # Remove off-screen obstacles
            if obs.obstacle_type == "diagonal":
                rad = math.radians(obs.angle)
                cos_r, sin_r = math.cos(rad), math.sin(rad)
                cx, cy = obs.center
                w, h = obs.width, obs.height
                corners = [(-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2)]
                rotated_corners = [(cx + x * cos_r - y * sin_r, cy + x * sin_r + y * cos_r) for x, y in corners]
                if max(x for x, y in rotated_corners) < 0:
                    try:
                        self.ids.obstacles_layout.remove_widget(obs)
                    except Exception:
                        pass
                    try:
                        self.obstacles.remove(obs)
                    except ValueError:
                        pass
                    continue
            else:
                if obs.right < 0:
                    try:
                        self.ids.obstacles_layout.remove_widget(obs)
                    except Exception:
                        pass
                    try:
                        self.obstacles.remove(obs)
                    except ValueError:
                        pass
                    continue

            # Collision detection (only when not paused)
            if obs.collides_with(player):
                # trigger hit pause safely (prevents retrigger)
                self.trigger_hit_pause()
                # break -> don't keep checking more collisions this frame
                break

        # --- Crosshairs update ---
        for cross in list(self.crosshairs):
            if cross.active and cross.tracking:
                cross.center_y = player.center_y
            cross.timer = getattr(cross, "timer", 0) + dt
            fire_delay = 3 if cross.tracking else 1.0
            if cross.timer >= fire_delay - 0.1 and cross.active and not getattr(cross, "sound_played", False):
                cross.sound_played = True
                self.play_sound(self.crosshair_sounds)
            if cross.timer >= fire_delay and cross.active:
                cross.active = False
                Clock.schedule_once(lambda _, y=cross.center_y: self.fire_missile(y), 0.3)
                Clock.schedule_once(lambda _, c=cross: self.remove_crosshair(c), 0.3)

        # --- Missiles update ---
        for missile in list(self.missiles):
            if not missile.move(dt, self.difficulty_multiplier):
                try:
                    self.ids.obstacles_layout.remove_widget(missile)
                except Exception:
                    pass
                try:
                    self.missiles.remove(missile)
                except ValueError:
                    pass
            else:
                px, py, pw, ph = self.ids.player.get_hitbox()
                mx, my, mw, mh = missile.get_hitbox()

                if (px < mx + mw and px + pw > mx and
                    py < my + mh and py + ph > my):
                    self.trigger_hit_pause()
                    break

        # --- Coin spawn & update ---
        self._coin_timer += dt
        if self._coin_timer >= self.COIN_INTERVAL:
            self._coin_timer = 0
            if random.random() < self.COIN_SPAWN_CHANCE:
                self.spawn_coin()

        # --- Update all coins ---
        for coin in list(self.coins):
            alive = coin.move(dt)

            # --- Player custom hitbox ---
            px, py, pw, ph = self.ids.player.get_hitbox()

            # --- Coin box (normal widget rect) ---
            cx, cy = coin.x, coin.y
            cw, ch = coin.width, coin.height

            # --- Inline AABB collision check (NO helper function needed) ---
            if px < cx + cw and px + pw > cx and py < cy + ch and py + ph > cy:
                coin.collected = True
                self.score += 100
                alive = False

            # Remove coin if collected or off-screen
            if not alive:
                try:
                    self.ids.obstacles_layout.remove_widget(coin)
                except Exception:
                    pass
                self.coins.remove(coin)
             
        if self.high_score > 0 and self.score > self.high_score and not getattr(self,  "_high_score_event_triggered", False):
            self.trigger_high_score_event()
            self._high_score_event_triggered = True
        
    # --- Obstacles & crosshairs ---
    def spawn_obstacle(self):
        if random.random() < self.SKIP_CHANCE:
            return
        obs = Obstacle()
        obs.size_hint = (None, None)
        obs_type = random.choice(["vertical", "horizontal", "diagonal"])
        obs.obstacle_type = obs_type
        buffer = self.width * 0.05
        min_y = self.height * self.BRIDGE_HEIGHT_RATIO + self.height * 0.05

        vertical_width = self.width * self.OBSTACLE_WIDTH_RATIO
        vertical_height_min = self.height * self.OBSTACLE_HEIGHT_MIN_RATIO
        vertical_height_max = self.height * self.OBSTACLE_HEIGHT_MAX_RATIO
        horizontal_width_min = self.width * 0.15
        horizontal_width_max = self.width * 0.35
        horizontal_height = self.height * self.OBSTACLE_HEIGHT_MIN_RATIO
        diagonal_width = self.width * self.OBSTACLE_WIDTH_RATIO
        diagonal_height_min = self.height * self.OBSTACLE_HEIGHT_MIN_RATIO
        diagonal_height_max = self.height * self.OBSTACLE_HEIGHT_MAX_RATIO

        if obs_type == "vertical":
            obs.width = vertical_width
            obs.height = random.randint(int(vertical_height_min), int(vertical_height_max))
            obs.x = self.width + buffer
            obs.y = random.randint(int(min_y), int(self.height - obs.height - 10))
        elif obs_type == "horizontal":
            obs.height = vertical_width
            obs.width = random.randint(int(horizontal_width_min), int(horizontal_width_max))
            obs.x = self.width + buffer
            obs.y = random.randint(int(min_y), int(self.height - obs.height - 10))
        else:
            obs.width = diagonal_width
            obs.height = random.randint(int(diagonal_height_min), int(diagonal_height_max))
            obs.angle = random.choice([45, -45])
            rad = math.radians(obs.angle)
            rotated_width = abs(obs.width * math.cos(rad)) + abs(obs.height * math.sin(rad))
            obs.x = self.width + rotated_width + buffer
            obs.y = random.randint(int(min_y), int(self.height - rotated_width - 10))

        with obs.canvas:
            Color(0.9, 0.2, 0.2, 1)
            if obs_type == "diagonal":
                obs.push = PushMatrix()
                obs.rot = Rotate(angle=obs.angle, origin=obs.center)
                obs.rect = Rectangle(pos=obs.pos, size=(obs.width, obs.height))
                obs.pop = PopMatrix()
            else:
                obs.rect = Rectangle(pos=obs.pos, size=(obs.width, obs.height))

        def update_rect(inst, val):
            inst.rect.pos = inst.pos
            inst.rect.size = inst.size
            if obs_type == "diagonal":
                inst.rot.origin = inst.center

        obs.bind(pos=update_rect, size=update_rect)
        self.ids.obstacles_layout.add_widget(obs)
        self.obstacles.append(obs)

    def spawn_crosshair(self, tracking=True):
        size = self.width * self.CROSSHAIR_SIZE_RATIO
        cross = Crosshair(size_hint=(None, None), size=(size, size))
        cross.tracking = tracking
        min_y = self.BRIDGE_HEIGHT + size
        max_y = self.height - size * 2
        cross.center_y = self.ids.player.center_y if tracking else random.randint(int(min_y), int(max_y))
        cross.x = self.width - size * 2
        self.ids.obstacles_layout.add_widget(cross)
        self.crosshairs.append(cross)

    def remove_crosshair(self, cross):
        if cross in self.crosshairs:
            try:
                self.ids.obstacles_layout.remove_widget(cross)
            except Exception:
                pass
            try:
                self.crosshairs.remove(cross)
            except ValueError:
                pass

    def fire_missile(self, y):
        # Don't spawn new missiles if we are in hit pause or already in game over
        if getattr(self, "hit_pause", False) or getattr(self, "game_over_triggered", False) or getattr(self, "_suppress_scheduled_actions", False):
            return

        missile = Missile(size_hint=(None, None),
                          size=(self.width * self.MISSILE_WIDTH_RATIO, self.height * self.MISSILE_HEIGHT_RATIO))
        missile.center_y = y
        missile.x = self.width
        w, h = missile.width, missile.height
        with missile.canvas:
            Color(1, 0.45, 0, 1)
            missile.triangle = Triangle(points=[missile.x+w, missile.y, missile.x+w, missile.y+h, missile.x, missile.y+h/2])
        def update_triangle(instance, val):
            x, y = instance.pos
            w, h = instance.size
            instance.triangle.points = [x+w, y, x+w, y+h, x, y+h/2]
        missile.bind(pos=update_triangle, size=update_triangle)
        self.ids.obstacles_layout.add_widget(missile)
        self.missiles.append(missile)
        self.play_sound(self.missile_sounds)

    # Spawn a coin
    def spawn_coin(self):
        coin = Coin(
            screen_width=self.width,
            screen_height=self.height,
            scroll_speed=300,   # horizontal speed
            period=3.0         # seconds per full up-down bounce
        )

        self.ids.obstacles_layout.add_widget(coin)
        self.coins.append(coin)

    # --- Hit pause / game over ---
    def trigger_hit_pause(self):
        if self.hit_pause or self._hit_pause_scheduled or self.game_over_triggered:
            return

        self._hit_pause_scheduled = True
        self.hit_pause = True
        self._suppress_scheduled_actions = True

        try:
            self._stored_player_velocity = self.ids.player.velocity_y
            self.ids.player.velocity_y = 0
        except Exception:
            self._stored_player_velocity = 0

        # Start music fade immediately, matching hit pause duration
        self.fade_music_out(duration=self.HIT_PAUSE_DURATION)

        self._hit_pause_event = Clock.schedule_once(self.end_hit_pause, self.HIT_PAUSE_DURATION)

    def end_hit_pause(self, dt=None):
        self._hit_pause_scheduled = False
        self._hit_pause_event = None
        self.hit_pause = False
        self.game_over_triggered = True

        # Update high score
        if self.score > self.high_score:
            self.high_score = self.score
            self.new_high_score = True
        else:
            self.new_high_score = False

        # Switch screen
        try:
            go_screen = self.manager.get_screen("game_over")
            go_screen.final_score = int(self.score)
            go_screen.high_score = int(self.high_score)
            go_screen.new_high_score = self.new_high_score
            self.manager.current = "game_over"
        except Exception:
            pass

    def fade_music_out(self, duration=1.0, on_complete=None):
        if not getattr(self, "bg_music", None):
            if on_complete:
                on_complete()
            return

        start_volume = float(getattr(self.bg_music, "volume", 1.0))
        elapsed = {"t": 0.0}
        fade_event = {"e": None}

        holder = getattr(self, "_fade_event_holder", None)
        if holder is None:
            self._fade_event_holder = {}
            holder = self._fade_event_holder
        if holder.get("e"):
            try:
                holder["e"].cancel()
            except Exception:
                pass
            holder["e"] = None

        def step(dt):
            try:
                elapsed["t"] += dt
                ratio = min(elapsed["t"] / duration, 1.0)
                new_volume = start_volume * (1.0 - ratio)
                self.bg_music.volume = max(0.0, new_volume)

                if ratio >= 1.0:
                    self.bg_music.stop()
                    self.bg_music.volume = start_volume
                    if fade_event["e"]:
                        fade_event["e"].cancel()
                    holder["e"] = None
                    if on_complete:
                        on_complete()
                    return False
                return True
            except Exception:
                if fade_event["e"]:
                    fade_event["e"].cancel()
                holder["e"] = None
                if on_complete:
                    on_complete()
                return False

        fade_event["e"] = Clock.schedule_interval(step, 1 / 30.0)
        holder["e"] = fade_event["e"]

    def game_over(self):
        """Fallback method if other code calls game_over() manually."""
        if self.game_over_triggered:
            return
        self.game_over_triggered = True
        try:
            self.manager.get_screen("game_over").final_score = int(self.score)
            self.manager.current = "game_over"
        except Exception:
            pass

    # --- Input ---
    def on_touch_down(self, touch):
        self.thrusting = True
        return True

    def on_touch_up(self, touch):
        self.thrusting = False
        return True

    def show_dialogue(self, text, portrait):
        # Prevent multiple dialogues
        if hasattr(self, "_current_dialogue") and self._current_dialogue in self.children:
            return

        scale_factor = 0.9

        # Dialogue box size
        box_width = self.width * 0.75 * scale_factor
        box_height = self.height * 0.3 * scale_factor
        spacing = 5  # space between portrait and text

        # Portrait size
        portrait_width = box_width * 0.4
        portrait_height = box_height

        # Padding for layout (left, bottom, right, top)
        layout_padding = [5, 5, 15, 5]  # extra 10px on right

        # Text width
        text_width = box_width - portrait_width - spacing - layout_padding[0] - layout_padding[2]

        # Dynamic font sizes
        font_size = sp(self.height * 0.035)
        name_font_size = sp(self.height * 0.025)

        # Container with background
        dialogue_container = BoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            width=box_width,
            height=box_height,
            spacing=spacing,
            padding=layout_padding,
            opacity=0
        )

        # Background rectangle
        with dialogue_container.canvas.before:
            Color(0, 0, 0, 0.35)
            dialogue_container.bg_rect = Rectangle(pos=dialogue_container.pos, size=dialogue_container.size)

        def update_bg_rect(instance, val):
            dialogue_container.bg_rect.pos = instance.pos
            dialogue_container.bg_rect.size = instance.size

        dialogue_container.bind(pos=update_bg_rect, size=update_bg_rect)

        # Portrait container (to hold portrait + name tag)
        portrait_container = Widget(size_hint=(None, None), width=portrait_width, height=portrait_height)

        portrait_path = resource_find(portrait)
        portrait_widget = Image(
            source=portrait_path if portrait_path else portrait,
            size_hint=(None, None),
            width=portrait_width,
            height=portrait_height,
            allow_stretch=True,
            keep_ratio=False
        )
        portrait_container.add_widget(portrait_widget)

        # Name tag overlay (Alan K)
        name_tag = Label(
            text="Alan K",
            font_size=name_font_size,
            size_hint=(None, None),
            width=portrait_width*0.5,
            height=name_font_size * 2.2,
            halign='right',
            valign='middle',
            color=(1, 1, 1, 0.5)
        )

        # Background for name tag
        with name_tag.canvas.before:
            Color(0, 0, 0, 0)
            name_tag.bg_rect = Rectangle(pos=name_tag.pos, size=name_tag.size)

        def update_name_bg(instance, val):
            name_tag.bg_rect.pos = instance.pos
            name_tag.bg_rect.size = instance.size

        name_tag.bind(pos=update_name_bg, size=update_name_bg)

        # Position the name tag overlapping bottom of portrait
        name_tag.pos = (0, 0)

        portrait_container.add_widget(name_tag)
        dialogue_container.add_widget(portrait_container)

        # Dialogue text
        text_widget = Label(
            text=text,
            halign='left',
            valign='middle',
            text_size=(text_width, box_height - layout_padding[1] - layout_padding[3]),
            size_hint=(None, None),
            width=text_width,
            height=box_height,
            font_size=font_size
        )
        dialogue_container.add_widget(text_widget)

        # Position bottom-left
        dialogue_container.pos = (0, 0)

        self._current_dialogue = dialogue_container
        self.add_widget(dialogue_container)

        # Fade-in animation
        Animation(opacity=1, duration=0.4).start(dialogue_container)

        # Auto-remove with fade-out after 5 seconds
        def remove(dt):
            if dialogue_container in self.children:
                Animation(opacity=0, duration=0.4).start(dialogue_container)
                Clock.schedule_once(lambda dt: self.remove_widget(dialogue_container), 0.45)
            self._current_dialogue = None

        Clock.schedule_once(remove, 4)

    def trigger_high_score_event(self):
        """Play a random high score dialogue and sound when the current score exceeds the previous high score."""
        if self.score > self.high_score:
            response = get_random_response()

            # Play preloaded sound
            sound = response.get("sound_obj")
            if sound and getattr(sound, "state", None) != "play":
                sound.stop()
                sound.play()

            # Show dialogue
            self.show_dialogue(response["text"], response["portrait"])

class JetpackApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(StartScreen(name="start"))
        sm.add_widget(GameScreen(name="game"))
        sm.add_widget(GameOverScreen(name="game_over"))
        return sm

if __name__ == "__main__":
    JetpackApp().run()
