# Fighter Game Widget (`game_fighter/game_widget.py`)

`FighterGame` is the core Kivy widget that drives menus, rendering, input, physics, AI, and match flow. Below is a function-by-function reference with signatures, parameters, behavior, and where results feed back into the code.

## Module helpers
- `keyname_from_event(keycode, codepoint) -> str`: Normalizes Kivy keydown events to readable names (e.g., arrow keys, space). Used in `_on_key_down`.
- `keyname_from_keyup(keycode) -> str`: Normalizes keyup events. Used in `_on_key_up`.
- `load_ryu_assets() / load_ken_assets() -> dict`: Return file paths for each animation state; consumed by `_init_fighters` and `_apply_selection`.

## Class: `FighterGame(Widget)`
### Construction / setup
- `__init__(**, debug_mode=False)`: Seeds state (stage size, control mode list, input managers, timers, UI groups), loads backgrounds, builds fighters, binds window/input events, and enters the main menu unless debug mode skips to play. Initializes camera, HUD groups, and schedules `update()`.
- `_init_fighters()`: Instantiates `Fighter` objects for P1/P2 with starting positions and sprite paths. Called during `__init__`.
- `_make_layer(path, idx, total, *, align="center", bottom=False, speed=None, is_floor=False, y_offset=0, scale_mode="fit_width", ref_w=None) -> dict`: Creates metadata for a background layer (texture, parallax speed, alignment). Used in `_load_stage`.
- `_reference_floor_y() -> float`: Computes a reference floor height based on window width to keep collision height consistent. Used in `_refresh_floor_scale`.
- `_refresh_floor_scale()`: Recomputes floor height/offsets when window size changes; updates background layers that depend on floor height. Called in `_on_size`.
- `_load_stage(key)`: Loads background/floor textures for the current stage, sets parallax layers, and resets floor values. Called on init and whenever stage changes.
- `_layout_bg_cover()`: Builds/updates a solid-color rect to cover empty areas behind parallax layers. Called in `_sync_draw` flows.
- `_build_scene()`: Creates ground rect and fighter drawables, attaches render layers, builds HUD, and syncs initial draw. Called during init and after stage/selection changes.
- `_on_size(...)`: Handles window resize; updates stage width, floor, HUD layout, background cover, and touch UI, then rerenders UI.
- `_attach_after_layers()`: Ensures the canvas groups (debug, FX, HUD, banners, UI, touch) are attached in the correct order (world vs. screen space). Called in init and after scene rebuilds.
- `_compute_sprite_scale() -> float`: Returns the current sprite render scale (defaults to `SPRITE_SCALE`). Used when setting fighter render scale.
- `_apply_sprite_scale()`: Applies `_compute_sprite_scale` to fighters. Called when resizing or rebuilding.
- `_sync_draw()`: Syncs fighter rectangles with current sprite textures/positions and camera. Called frequently in update/render flows.
- `_draw_debug_boxes()`: If `show_hitboxes` is enabled, clears and redraws hurtbox/hitbox overlays using `Rectangle` primitives. Otherwise clears overlays. Called in `update`.

### HUD / UI rendering
- `_build_hud()`: Initializes health/timer/name HUD elements and caches textures. Called during scene build.
- `_layout_hud()`: Positions HUD elements based on window size. Called in `_on_size` and `_sync_draw` flows.
- `_render_timer(top_margin=None, bar_h=None, gap=None)`: Draws the round timer UI with optional layout overrides. Called when timer changes.
- `_render_names(top_margin=None)`: Draws player names in the HUD. Called after selections and layout changes.
- `_render_round_counters(top_margin=None)`: Renders round win indicators. Called when rounds update.
- `_update_health_bars()`: Updates health bar visuals based on fighter HP. Called during HUD updates and after hits.
- `_health_bar_height(half_w) -> float`: Computes bar height for scaling health bars. Used by `_layout_hud`.
- `_health_texcoords(tex, ratio, anchor="left") -> list`: Returns texture coordinates cropped to a given ratio for health depletion. Used by `_update_health_bars`.
- `_clear_ui()`: Clears UI groups (menus/banners). Used before rendering menus.
- `_load_texture(path) -> Texture|None`: Safe texture loader with error handling. Used for HUD assets.
- `_label_kwargs(font_px) -> dict`: Returns kwargs for Kivy label textures (font, size). Used by label helpers.
- `_measure_label(text, font_px) -> Texture`: Builds a texture for measuring text; used by `_draw_label` and menu rendering.
- `_draw_label(text, x, y, font_px=48, color=(1,1,1,1))`: Draws text into the main UI group. Used throughout menus/HUD.
- `_draw_label_custom_group(group, text, x, y, font_px=24, color=(1,1,1,1))`: Same as `_draw_label` but targets a custom group. Used in HUD.
- `_add_menu_background()`: Adds menu background layers (logo/backdrop). Called by menu renderers.
- `_draw_logo(y, max_w=None, max_h=None, scale=1.0) -> Rectangle|None`: Draws the game logo, respecting size constraints. Used in main menu rendering.
- `_get_portrait_tex(path) -> Texture|None`: Loads/caches character portrait textures. Used in select grids.
- `_center_label(text, y, font_px=48, color=(1,1,1,1)) -> (w, h)`: Centers text horizontally in the UI. Used in menus.
- `_render_main_menu()`: Draws the main menu (logo, Play button, control mode toggle, prompts). Records button bounds for touch handling.
- `_render_select_grid(title, options, selected_idx)`: Renders character/stage selection grids with hover/selection borders and prompts.
- `_render_character_select()`: Calls `_render_select_grid` with character options.
- `_render_stage_select()`: Calls `_render_select_grid` with stage options.
- `_render_current_ui()`: Switches between main menu, character select, stage select, or clears UI based on `state`.

### Touch overlay
- `_draw_touch_button(x, y, size, label)`: Draws a semi-transparent touch button (used for D-pad/actions) into `touch_group`.
- `_layout_touch_ui()`: Clears/rebuilds on-screen touch controls when control mode is “touch” and game state is in-play/round-over/match-over. Stores button hitboxes in `touch_button_boxes` for input detection.

### Navigation / state transitions
- `_enter_main_menu() / _enter_character_select() / _enter_stage_select()`: Set `state`, render appropriate UI, and refresh touch overlay.
- `_move_character_cursor(direction)` / `_move_stage_cursor(direction)`: Advance selection indices modulo option count; re-render grids.
- `control_mode` (property): Returns current control mode string from `control_modes`.
- `_toggle_control_mode(delta=1)`: Cycles control mode list, resets inputs, and re-renders UI/touch overlay.
- `_option_index_from_touch(x, options) -> int|None`: Maps a touch X coordinate to the nearest selection index. Used in `_handle_touch_menu`.
- `_handle_touch_menu(touch) -> bool`: Handles taps in menus to play/select control mode or confirm selections; returns True if consumed.

### Input handling
- `_action_from_keyname(name) -> str|None`: Maps key names to logical menu actions. Used in `_on_key_down`.
- `_handle_menu_action(action) -> bool`: Processes menu navigation/confirmation; returns True if handled. Used by keyboard/controller handlers.
- `_queue_jump()` / `_queue_attack()`: Set flags to trigger jump/attack at the next input application frame. Used by multiple input sources.
- `_on_key_down(window, keycode, scancode, codepoint, modifiers)`: Handles keyboard presses; routes menu actions or sets directional/attack actions in `InputManager`.
- `_on_key_up(window, keycode, *args)`: Clears keyboard actions from `InputManager`.
- `_on_joy_axis(window, stickid, axisid, value)`: Maps joystick axes (0 = horizontal, 1 = vertical) to actions with deadzone handling. Triggers jump on up press.
- `_on_joy_hat(window, stickid, hatid, value)`: Maps D-pad hats to left/right/up/down, also steering menus.
- `_on_joy_button_down(window, stickid, buttonid)`: Maps controller buttons to jump/attack/confirm based on IDs; respects menus when not playing.
- `_on_joy_button_up(window, stickid, buttonid)`: Clears controller actions.
- `_actions_from_touch(touch) -> set`: Returns actions whose on-screen buttons intersect a touch (only in touch mode). Used by touch handlers.
- `_apply_touch_actions(touch, actions)`: Updates `InputManager` per touch source and triggers queued jump/attack for up/punch/kick. Maintains per-touch action sets.
- `on_touch_down(touch) / on_touch_move(touch) / on_touch_up(touch)`: Override Kivy touch events; handle menus or, in touch mode, map touches to button actions via `_actions_from_touch`.
- `_apply_input_p1(dt)`: Applies aggregated input to P1: queued jump/attack, then movement left/right; otherwise stops. Called each frame in `update`.

### AI and collision
- `_ai_update(dt)`: AI for P2 using a finite-state machine (approach/pressure/evade) plus a 1D greedy path step (A*-style on a line) toward targets. State changes only when a think timer elapses to reduce jitter; evasive state triggers when cornered/pressured to avoid stun-lock; pressure state pokes with a slower cooldown; close-range idling is broken by forcing a poke if idle; jumps are heavily throttled (one per state cycle with a cooldown); long-range idle is broken up by occasional pressure so the AI engages. Called each frame during play.
- `aabb(a, b) -> bool` (static): Axis-aligned bounding-box overlap test. Used in `_check_hit`.
- `_check_hit(attacker, defender)`: Retrieves hitbox/hurtbox, checks overlap, applies damage/knockback, sets hitstun/defeat/victory, and triggers camera shake/banners. Called each frame for both attacker/defender.

### Banners / round flow
- `_show_banner(text, seconds=None, font_px=72)`: Displays overlay text; optionally schedules auto-hide. Used for round intros, win/lose, fight overlays.
- `_hide_banner(*args)`: Clears banner group. Used when resuming play or after timers.
- `_show_fight_overlay(duration=2.0)`: Shows “FIGHT!” overlay for a duration, then hides. Used in round intro sequencing.
- `_reset_round_data()`: Resets timers, HP, FX, attack state, and redraws HUD/timer/round counters.
- `_end_round(winner)`: Sets `round_over`, updates win counts, shows banner, and schedules next round or match end.
- `_start_next_round()`: Increments round, resets round data, queues new round intro.
- `_resume_play(hide_banner=True)`: Hides banner (optional) and sets state to `playing`.
- `_end_match()`: Shows victory/defeat banner and sets state to `match_over`.
- `_reset_match()`: Starts a new match (clears UI, resets selections, rebuilds scene).
- `_apply_selection()`: Applies selected character/stage assets, reloads sprites, updates names/window title, and reloads stage assets.
- `_start_match()`: Clears UI, resets inputs, applies selection, rebuilds scene, sets initial state/round counters, queues round intro. Called from stage select confirmation.
- `_handle_defeat_impacts()`: Reads `defeat_landing_event` flags from fighters and triggers camera shake accordingly. Called each frame.
- `_queue_round_intro(round_number, stage_name=None)`: Schedules “Round X” and “Fight” overlays and resumes play after intro durations.

### Main loop / layout
- `update(dt)`: Core per-frame loop. If not playing, still updates fighters, camera shake, background cover, and draw sync. During play: applies input, updates AI, ticks timer, updates fighters, resolves collisions, handles defeat impacts, updates camera shake, debug boxes, backgrounds, and draw sync.
- `_start_positions() -> (p1_x, p2_x)`: Computes initial fighter X positions based on stage width and sprite size. Used in `_init_fighters`.
- `_separate_fighters()`: Pushes fighters apart horizontally when hurtboxes overlap to avoid stacking. Called each frame.
- `_trigger_shake(strength=14, duration=0.32)`: Starts camera shake; used on hits/defeat impacts.
- `_update_shake(dt)`: Advances camera shake timers/offsets. Called each frame.
- `_update_camera()`: Computes and applies camera transforms (scale/translate + shake) based on fighter positions. Used in `_sync_draw`.
