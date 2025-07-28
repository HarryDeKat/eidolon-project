# This module manages the state for the "Themed Weeks" or story arcs feature.

import os
import json
import ai_generators
from config import THEME_STATE_FILE

def get_active_theme():
    """Reads theme_state.json to see if a theme is in progress."""
    if not os.path.exists(THEME_STATE_FILE):
        return None
    try:
        with open(THEME_STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None

def start_new_theme():
    """
    Calls the AI to generate a theme and writes it to theme_state.json.
    """
    theme_data = ai_generators.generate_story_arc_theme()
    if theme_data:
        state = {
            "theme_name": theme_data["theme_name"],
            "stories_in_arc": int(theme_data["stories_in_arc"]),
            "stories_completed": 0
        }
        with open(THEME_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=4)
        return state
    return None

def update_theme_progress():
    """
    Increments the count of stories completed for the current theme.
    If the arc is complete, clears the theme.
    """
    state = get_active_theme()
    if state:
        state["stories_completed"] += 1
        if state["stories_completed"] >= state["stories_in_arc"]:
            print(f"Story arc '{state['theme_name']}' is now complete!")
            clear_theme()
        else:
            with open(THEME_STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=4)

def clear_theme():
    """Deletes theme_state.json when an arc is complete."""
    if os.path.exists(THEME_STATE_FILE):
        os.remove(THEME_STATE_FILE)
        print("Active theme cleared.")