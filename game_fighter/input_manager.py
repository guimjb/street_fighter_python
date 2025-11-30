class InputManager:
    """Track input actions coming from multiple sources (keyboard, touch, controller)."""

    ACTIONS = ("left", "right", "up", "down", "punch", "kick", "special")

    def __init__(self):
        self.state = {action: False for action in self.ACTIONS}
        self._sources = {action: set() for action in self.ACTIONS}

    def set(self, action, value, source="default"):
        """
        Set or clear an action for a specific source.

        Returns True when the action transitions from inactive to active.
        """
        if action not in self._sources:
            return False

        was_active = self.state[action]
        if value:
            self._sources[action].add(source)
        else:
            self._sources[action].discard(source)

        self.state[action] = bool(self._sources[action])
        return not was_active and self.state[action]

    def clear_source(self, source):
        """Remove all actions coming from a given source (e.g., when a touch ends)."""
        for action in self.ACTIONS:
            self._sources[action].discard(source)
            self.state[action] = bool(self._sources[action])

    def reset(self):
        self.state = {action: False for action in self.ACTIONS}
        self._sources = {action: set() for action in self.ACTIONS}

    def get(self, action):
        return self.state.get(action, False)
