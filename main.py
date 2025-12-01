from functools import partial

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager

from game_fighter.game_widget import FighterGame


class MenuScreen(Screen):
    def __init__(self, on_select, **kwargs):
        super().__init__(name="menu", **kwargs)
        layout = BoxLayout(orientation="vertical", padding=[40, 60, 40, 60], spacing=20)

        title = Label(text="Gui Machado - Alief Radava", font_size="28sp", bold=True, size_hint=(1, 0.3))
        subtitle = Label(text="Choose a game to play", font_size="16sp", size_hint=(1, 0.2))

        button_box = BoxLayout(orientation="vertical", spacing=15, size_hint=(1, 0.5))
        jetpack_btn = Button(text="Jetpack Cat")
        fighter_btn = Button(text="Street Fighter Python")

        jetpack_btn.bind(on_release=partial(on_select, "jetpack"))
        fighter_btn.bind(on_release=partial(on_select, "fighter"))

        button_box.add_widget(jetpack_btn)
        button_box.add_widget(fighter_btn)

        layout.add_widget(title)
        layout.add_widget(subtitle)
        layout.add_widget(button_box)

        self.add_widget(layout)


class GameSelectorApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = None
        self.jetpack_app = None
        self.jetpack_root = None
        self.jetpack_screen = None
        self.fighter_screen = None

    def build(self):
        Window.title = "Retro System"
        Window.clearcolor = (0.03, 0.03, 0.05, 1)
        self.screen_manager = ScreenManager(transition=FadeTransition(duration=0.2))
        self.screen_manager.add_widget(MenuScreen(on_select=self.launch_game))
        # Explicitly start on the menu so mobile builds don't jump straight into a game.
        self.screen_manager.current = "menu"
        return self.screen_manager

    def on_start(self):
        # Extra guard in case platform defaults ever bypass the initial screen choice.
        if self.screen_manager:
            self.screen_manager.current = "menu"

    def launch_game(self, game_key, *_):
        if game_key == "jetpack":
            self._show_jetpack()
        elif game_key == "fighter":
            self._show_fighter()

    def _show_fighter(self):
        if not self.fighter_screen:
            self.fighter_screen = Screen(name="fighter")
            self.fighter_screen.add_widget(FighterGame())
            self.screen_manager.add_widget(self.fighter_screen)

        Window.title = "2D Fighter \u2014 Refactored"
        self.screen_manager.current = "fighter"

    def _show_jetpack(self):
        if not self.jetpack_screen:
            # Lazy import so we only load the Jetpack assets when needed.
            from jetpackgame.app.jetpackgame import JetpackApp

            self.jetpack_app = JetpackApp()
            jetpack_root = self.jetpack_app.build()
            self.jetpack_root = jetpack_root
            self.jetpack_app.root = jetpack_root
            # Expose launcher helpers so KV can call back out
            self.jetpack_app.return_to_menu = self.return_to_menu
            self.jetpack_app.jetpack_root = jetpack_root
            self.jetpack_screen = Screen(name="jetpack")
            self.jetpack_screen.add_widget(jetpack_root)
            self.screen_manager.add_widget(self.jetpack_screen)

        Window.title = "Jetpack Cat"
        self.screen_manager.current = "jetpack"

    def return_to_menu(self, *_):
        # If we were inside Jetpack, reset it to the start screen to stop any running loops.
        if self.jetpack_root is not None:
            try:
                self.jetpack_root.current = "start"
            except Exception:
                pass
        Window.title = "Retro System"
        self.screen_manager.current = "menu"


if __name__ == "__main__":
    GameSelectorApp().run()
