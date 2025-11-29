# Entry point for the fighter game. Classes now live in dedicated modules for clarity.
try:
    # Package import (preferred)
    from .fighter_app import FighterApp
except ImportError:
    # Fallback for running as a loose script
    from fighter_app import FighterApp


if __name__ == "__main__":
    FighterApp().run()