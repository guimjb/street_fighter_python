# Fighter App (`game_fighter/fighter_app.py`)

## Purpose
`fighter_app.py` hosts the Kivy `App` subclass (`FighterApp`) that bootstraps the game. It configures the window title, reads the debug flag, and builds the root widget (`FighterGame`). Having this entry layer keeps Kivy-specific setup isolated from gameplay logic, so `game_widget.py` can focus on the game itself.

## Why it exists
- **Separation of concerns:** Splits window/app lifecycle concerns (title, debug flag, window bindings) from the gameplay widget and models.
- **Multiple entry points:** Both `main.py` and `fighter_game.py` simply instantiate/run `FighterApp`, keeping those files tiny and reusable across platforms.
- **Debug/production toggle:** Reads `FIGHTER_DEBUG` so you can skip menus and jump into a match when needed without touching game code.
- **Platform-friendly sizing:** Leaves window sizing to the platform (desktop or mobile) instead of hard-coding a resolution, while still setting the window title.

## Responsibilities
- Create and return the `FighterGame` widget via `build()`.
- Set the window title (`Window.title`).
- Respect `FIGHTER_DEBUG=1` to enable debug mode in `FighterGame`.

## When to edit
- Adjust app-level flags (future CLI args/env vars).
- Add platform-specific window tweaks (fullscreen toggles, orientation locks) without polluting gameplay code.
