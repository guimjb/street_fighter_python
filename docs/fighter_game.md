# Fighter Game (`game_fighter/fighter_game.py`)

## Purpose
`fighter_game.py` is the package-level entry point for the fighter. It exists so the game can be launched with `python -m game_fighter.fighter_game` or by running the file directly, while keeping all gameplay code inside the package.

## Why it exists
- **Clean entry point:** Keeps startup logic minimal and separate from gameplay code.
- **Flexible invocation:** Supports both module-style runs (`python -m ...`) and direct file runs, adding the project root to `sys.path` when needed.
- **Shared across launchers:** `main.py` and any external scripts can import/run `FighterApp` without duplicating setup.

## Responsibilities
- Import and run `FighterApp`.
- Add the project root to `sys.path` when executed directly so package imports resolve.
- Guard execution with `if __name__ == "__main__":` to avoid side effects on import.

## When to edit
- To change how the app is launched (e.g., CLI flags or env-driven options).
- To add lightweight bootstrap behavior (profiling hooks, logging setup) without touching gameplay code.
