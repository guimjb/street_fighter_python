# USF Programming Design – Submission Deliverables

Provide all of the following in your final handoff.

## Individual Game Components
- Complete source code (Python/Kivy) for the fighter, including gameplay, AI, physics, input, and state management.
- All assets used by the game: sprites, stages, fonts, UI art, and sounds (`assets/`).
- Controls guide for keyboard/controller/touch (`README.md` controls section and `CONTROLS.txt`).
- Module documentation (`docs/`): `fighter_game.md`, `fighter_app.md`, `game_widget.md`, `fighter.md`, `sprite_anim.md`, `input_manager.md`, `constants.md`, `buildozer.md`, and this deliverables file.
- Build configuration and scripts: `buildozer.spec`, desktop entry points (`main.py`, `game_fighter/fighter_game.py`), and any helper tools in `tools/`.
- Prebuilt Android package: `streetfightherpython.apk` in the repo root for sideload/testing.

## Integrated System
- Runnable builds:
  - Desktop: run via `python -m game_fighter.fighter_game` (or `python game_fighter/fighter_game.py`).
  - Android: APK built from `buildozer.spec` (included as `streetfightherpython.apk`).
- Installation/usage instructions: steps in `README.md` and `docs/buildozer.md` (WSL/venv setup, dependencies, build commands).
- User manual: controls and menu flow in `README.md`/`CONTROLS.txt`.



- System test/validation notes: document playtest outcomes and any automated checks you performed.
- Performance benchmarks/profiling (if required): note any measurements taken (FPS, load times) and the method/tools used.

## Documentation
- Project proposal/goal: Street Fighter–style 2D fighter built with Python/Kivy and touch/keyboard/controller support.
- Design/architecture documentation: module docs in `docs/`, AI algorithm description (state machine + greedy path step) in `docs/game_widget.md`, build packaging in `docs/buildozer.md`.
- Final project report: summarize architecture, algorithms (AI decision-making, collision, physics), testing results, and performance notes.
- Presentation slides (if required by course): features, architecture, AI approach, controls, and screenshots.
