"""Entry point for the fighter game."""

from pathlib import Path
import sys

# Allow running this file directly (python game_fighter/fighter_game.py)
if __package__ is None and __name__ == "__main__":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from game_fighter.fighter_app import FighterApp

if __name__ == "__main__":
    FighterApp().run()
