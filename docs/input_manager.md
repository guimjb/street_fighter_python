# Input Manager (`game_fighter/input_manager.py`)

`InputManager` centralizes action state coming from multiple sources (keyboard, controller, touch). It keeps per-action, per-source flags so overlapping inputs stack correctly (e.g., two touches holding “left” still count as active until both end).

## Class: `InputManager`

### Attributes
- `ACTIONS`: Tuple of supported logical actions (`left`, `right`, `up`, `down`, `punch`, `kick`, `special`).
- `state`: Dict of action -> bool indicating whether each action is currently active across all sources.
- `_sources`: Dict of action -> set of source identifiers currently asserting that action.

### Methods
- `set(action, value, source="default") -> bool`: Turn an action on/off for a specific source. Updates `_sources` and recomputes `state[action]`. Returns `True` only when the action transitions from inactive to active (used to trigger one-time events like jump/attack in `game_widget.py`).
- `clear_source(source)`: Removes all actions associated with a given source (e.g., when a touch ends), updating `state` accordingly. Called from touch up handlers in `game_widget.py`.
- `reset()`: Clears all state and source sets. Used when starting matches or toggling control modes.
- `get(action) -> bool`: Returns current active state for an action. Read by input application code in `game_widget.py` when moving/acting the player.
