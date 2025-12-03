# Individual Game Documentation - 2D Fighter

## Overview
- Street Fighter-style 1v1 fighter built with Kivy; runs via the Retro System launcher (`main.py`) or directly through `FighterApp`. Default control mode is touch for mobile, but keyboard/controller input is fully supported.
- Full flow: title menu -> options -> character select (Ryu/Ken) -> stage select (Boat/Military) -> round intros with narrator VO -> best-of-3 match (60s timer) -> victory menu or continue/game-over countdown.
- Gameplay: single punch attack with startup/active/recovery, gravity and jump, hitstun/knockback, defeat/victory bounces, camera shake, and a lightweight AI opponent driving the second fighter.
- HUD: shared single health bar that drains from both ends toward center while still showing both names/pips; round timer sits below; win pips on both sides. Touch UI appears only in play/round-over states when touch mode is active.
- Audio: title/select/victory/continue/game-over music plus rotating stage tracks; narrator callouts for round numbers/final/fight/perfect/win/lose; menu SFX for scroll/confirm/game start.
- Build/launch: desktop via `python -m game_fighter.fighter_game` (or from the Retro System menu) and Android via `buildozer.spec`; prebuilt APK `streetfightherpython.apk` lives in the repo root.

## Systems and Algorithms
- **State flow:** `main_menu`, `options`, `character_select`, `stage_select`, `playing`, `round_over`, `match_over_win`, `continue`, `game_over`. `FIGHTER_DEBUG=1` jumps straight into play with default selections.
- **Input:** `InputManager` merges keyboard, controller, and touch. On-screen D-pad + punch button render only when touch mode is selected; menu input shares confirm/arrow/tap handling.
- **Fighters:** `Fighter` tracks movement, facing, attack state machine (startup -> active -> recovery), hitstun, defeat/victory, and per-frame landing events for screen shake. Hit/hurt boxes prefer JSON frame metadata (`ryu_frames.json`, `ken_frames.json`) with heuristics as fallback.
- **Collision/damage:** Axis-aligned overlap test drives hits; on connect, apply damage, knockback, and hitstun; trigger camera shake and SFX; defeat triggers a two-impact landing sequence and victory/defeat animations.
- **AI:** Finite-state machine (approach/pressure/evade/idle) with timed decision windows and a greedy 1D path step toward/away from targets. Jump/attack cooldowns reduce jitter; occasional long-range pressure so the AI re-engages.
- **Camera/HUD:** Smoothed camera follow with configurable zoom and shake overlay. Shared health bar crops from both ends; timer, names, and round pips rerender as values change. Round/fight overlays stay visible for the duration of narrator audio (round intro + 0.5s buffer, then fight.mp3 length).
- **Audio system:** Music library for title/select/victory/continue/game-over plus rotating stage tracks; narrator VO sequenced per round; options menu lets you adjust music (capped by `music_base`) and SFX volumes.
- **Stages:** Boat uses two background layers plus floor; Military has a single background + floor. Floors rescale to window width using a reference floor height to keep jump/collision feel stable across resolutions. Parallax is intentionally disabled to avoid seams on mobile-layers are scaled/static.
- **Menus:** Title menu with Play/Options/Home (returns to launcher); select grids for fighters/stages with portraits; options for volume/control mode; win menu offers restart/menu; continue screen gives 10s to choose Stand Strong or Give Up before game over.

## Assets
- Fighters: `assets/ryu_sprites_project/*`, `assets/ken_sprites_project/*`, portraits inside each folder, and frame metadata in `ryu_frames.json`/`ken_frames.json`.
- UI/audio: HUD textures `assets/Menu/healthbar_back.png`, `assets/Menu/healthbar_front.png`, logo/presplash `assets/Menu/project_logo.png`; narrator VO `assets/projectsounds/narrator/*.mp3`; tracks `assets/projectsounds/track/*.mp3`; menu/effect sounds in `assets/projectsounds/effect/*.wav` and `assets/projectsounds/characters/*.wav`.
- Stages: Boat art under `assets/boat_stage_project/`; Military art under `assets/military_stage_project/`.
- Android: `buildozer.spec` plus prebuilt `streetfightherpython.apk` for sideloading/tests.

## Known Limitations / Next Steps
- Single attack per character; no combos, blocking, throws, or specials yet.
- Background parallax is disabled; layers are static to avoid seams/artifacts on varied aspect ratios.
- AI is simple and deterministic; no difficulty scaling or adaptive behavior.
- No pause menu or persistence of options; control/volume choices reset each run.
- Camera is limited to horizontal clamping via stage bounds; no wider arenas or scrolling stages.
