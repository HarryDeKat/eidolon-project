# The Eidolon Project

**"Creative as Black Mirror, stunning as van Gogh, beautiful as nature."**

This project is a Python-based AI script that generates a unique, psychologically-rich narrative each time it is run. It is designed to be a source of daily introspection, learning, and literary art.

The AI, acting as "The Curator," first conceives a unique creative brief—combining a psychological concept with an inventive format. It then writes a story based on that brief, followed by a "Curator's Note" that unpacks the underlying theme.

All generated stories are compiled into a single `rss.xml` file, creating a personal, ever-growing anthology that can be read in any RSS reader.

## Features

-   **Creative Autonomy**: The AI has complete freedom to choose its theme, format, and narrative style.
-   **Psychological Depth**: Each story is built around a core concept from psychology, philosophy, or cognitive science.
-   **Intelligent Variety**: The script keeps a history of past stories to ensure new entries are fresh and avoid repetition.
-   **RSS Feed Output**: All stories are accessible in a standard RSS feed, with the newest appearing at the top.
-   **High-Quality Generation**: Uses a two-step prompting process with Google's Gemini model to first brainstorm an idea and then execute it with literary focus.

## Setup Instructions

### 1. Prerequisites

-   Python 3.7+
-   An API key for the Google Gemini API. You can get one from [Google AI Studio](https://aistudio.google.com/app/apikey).

### 2. Installation

Clone or download the project files into a single directory. Then, install the required Python library:

```bash
pip install google-generativeai
```

### 3. Configuration

Open the `config.py` file and replace `"YOUR_GEMINI_API_KEY_HERE"` with your actual Google Gemini API key.

```python
# config.py
API_KEY = "YOUR_GEMINI_API_KEY_HERE"
```

### 4. Running the Script

Navigate to the project directory in your terminal and run the main script:

```bash
python eidolon_project.py
```

The first time you run it, it will create two new files:
-   `history.json`: A log of all generated stories.
-   `rss.xml`: The RSS feed file.

Each subsequent run will add a new story to both of these files.

### 5. Reading the Stories

You can add the generated `rss.xml` file to your favorite RSS reader (like Feedly, Inoreader, or a local client). Most readers allow you to subscribe to a local file. This will give you a beautiful, chronological view of your personal story collection.