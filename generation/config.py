# config.py
# Store API keys, model names, and other configuration variables.

import os

# --- CORE CONFIGURATION ---

# Your Google Generative AI API Key
# Get a key from Google AI Studio: https://aistudio.google.com/app/apikey
# It is recommended to set this as an environment variable for security.
API_KEY = os.environ.get('GEMINI_API_KEY', "YOUR_GEMINI_API_KEY_HERE")

# --- FEATURE TOGGLES ---

# Set to False to disable AI image generation and save on API costs.
ENABLE_IMAGE_GENERATION = False

# --- MODEL CONFIGURATION ---
# We use a powerful model for the main story writing and a faster, cheaper
# model for smaller tasks like generating briefs, themes, and summaries.

# The primary model for creative writing. (e.g., "gemini-1.5-pro-latest")
MAIN_TEXT_MODEL = "gemini-2.5-pro"

# A faster model for brainstorming, summarization, and brief generation. (e.g., "gemini-1.5-flash-latest")
FAST_TEXT_MODEL = "gemini-2.5-flash"

# The model for generating cover art. (e.g., "imagen-3")
IMAGE_MODEL = "imagen-3"


# --- FILE PATHS ---

HISTORY_FILE = "history.json"
THEME_STATE_FILE = "theme_state.json"
RSS_FILE = "../static/rss.xml"
STORIES_DIR = "../content/stories/"
ART_DIR = "../static/art/"