import os

from kivy.app import App
from kivy.core.window import Window

try:
    from .game_widget import FighterGame
except ImportError:
    from game_widget import FighterGame


class FighterApp(App):
    def build(self):
        debug_mode = os.environ.get("FIGHTER_DEBUG", "0") == "1"
        # 16:9 baseline
        Window.size = (1920, 1080)
        Window.title = "2D Fighter — Refactored"
        return FighterGame(debug_mode=debug_mode)
