# 2D Fighter — Mid‑Project Package

## Repository layout
```
Source Code/
  fighter_game.py                      # main script (unchanged)
  assets/
    kobold/with_outline/IDLE.png
    kobold/with_outline/RUN.png
    kobold/with_outline/ATTACK 1.png
    forest/Background layers/*.png
Documentation/
  (see docs/ in this package)
Test Results/
  (fill with pytest and profiling outputs)
```

> Note: For the unified system, our group decided to focus on our individual games first.
> Integration (menu, consistent controls, Raspberry Pi packaging) is among the **last steps**
> we are planning to take for the project.

## Build & Run (desktop)
1. Ensure Python 3.10+
2. `pip install kivy kivy_deps.sdl2 kivy_deps.glew kivy_deps.angle`
3. Run:
   ```bash
   python fighter_game.py
   ```

## Controls
- Move: A / D (or Left / Right)
- Jump: W (or Up)
- Attack: J (or Space)
- Restart after match over: R / Enter / Space

## What’s included in this package
- `docs/Individual_Game_Documentation.md` – development process, algorithms, implementation.
- `docs/Integration_Status_And_Plan.md` – current status and plan for unified system.
- `docs/User_Manual.md` – how to run and play the game.
- `docs/System_Test_Results.md` – templates for stability/performance results.
- `tests/test_fighter_game.py` – unit tests (logic‑only).
- `profiling/PROFILE_GUIDE.md` – CPU profiling instructions and reporting format.
- `packaging/RPi_SETUP.md` – Raspberry Pi setup/packaging notes.
- `presentation/SLIDES_OUTLINE.md` – suggested slide outline for the mid/final presentation.

