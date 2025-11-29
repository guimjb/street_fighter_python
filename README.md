# Retro System - 2D Fighter

Arcade-style 2D fighter built with Kivy featuring character and stage select, sprite sheet animation, HUD, and a simple AI opponent.

## Requirements
- Python 3.10+
- Runtime: `kivy` (plus `kivy_deps.sdl2`, `kivy_deps.glew`, `kivy_deps.angle` on Windows)
- Tools: `Pillow` for the helper scripts in `tools/`

## Quick start
1. (Optional) create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install kivy kivy_deps.sdl2 kivy_deps.glew kivy_deps.angle pillow
   ```
3. Launch the game from the repository root:
   ```bash
   python -m game_fighter.fighter_game
   # or: python game_fighter/fighter_game.py
   ```
4. Set `FIGHTER_DEBUG=1` to skip menus and jump straight into a match.

## Controls
- Main menu: Enter/Space to start character select.
- Character select: A/Left/Up and D/Right/Down to change fighter, Enter/Space to continue.
- Stage select: A/Left/Up and D/Right/Down to change stage, Enter/Space to start.
- During match: A or Left to move left, D or Right to move right, W or Up to jump, J or Space to attack.
- After match: R/Enter/Space to restart, M/Esc/Backspace to return to main menu.

## Project structure
- `game_fighter/` - Python package for the game.
  - `fighter_game.py` - Entry point that instantiates the Kivy app.
  - `fighter_app.py` - Configures the window (1920x1080 baseline) and builds the main widget.
  - `game_widget.py` - Core gameplay widget: menu flow, stage loading, HUD rendering, parallax layers, camera, AI logic, input handling, and the main update loop.
  - `fighter.py` - Fighter model: movement and gravity, attack state machine, hit/hurt boxes, victory/defeat handling, and sprite swapping.
  - `sprite_anim.py` - Sprite sheet helper that slices textures into frames, advances animations, and exposes UV coordinates.
  - `constants.py` - Shared tuning values for sprite scale, physics scale, hitbox sizes, and stage margins.
  - `__init__.py` - Package marker.
- `assets/` - Game art and UI.
  - `Ryu Sprites Project/` - Ryu animation sheets (`Idle.png`, `Walk.png`, `Jump.png`, `Right Punch.png`, `Hit.png`, `Defeat.png`, `Victory 1/2.png`, `RyuPortrait.png`).
  - `Ken Sprites Project/` - Ken animation sheets (idle/run/jump/punch/hit/defeat/victory) and portrait.
  - `Boat Stage Project/` - Boat stage background layers and floor texture.
  - `Military Stage Project/` - Military stage background and floor.
  - `Menu/` - Project logo and fight button art for the main menu.
  - `Fonts/` - `StreetFont.ttf` used for HUD and banners.
  - `Text and Health Bar/` - Atlas for UI elements and health bar.
- `ryu_frames.json`, `ken_frames.json` - Generated frame metadata for slicing the Ryu and Ken sprite sheets; consumed by `fighter.py`.
- `tools/` - Utility scripts.
  - `slice_sprites.py` - Auto-slice horizontal sprite sheets into frame rectangles and emit JSON metadata.
  - `atlas_inspect.py` - Detect non-transparent regions in an atlas to map UI pieces (prints bounding boxes).
- `Game Showcase.mp4` - Sample gameplay footage.
- `Individual_Game_Documentation.md` - Design and implementation notes for this fighter game.
- `_tmp/` - Scratch space (ignored by Git; currently empty).
- `.gitignore` - Ignores the virtual environment, VS Code settings, and `_tmp/`.
- `.vscode/settings.json` - Local editor configuration.
- `.venv/` - Local virtual environment (not required if you manage envs elsewhere).

## Development notes
- Assets are loaded relative to the repository root; run commands from this directory so paths resolve correctly.
- The AI is intentionally lightweight; tweak ranges and timers in `game_widget.py` to change behavior.
- Hitboxes/hurtboxes can be adjusted in `constants.py` and per-frame metadata in the frame JSON files.
