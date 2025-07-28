# ai_generators.py
# All functions that interact with the Google Generative AI API.

import os
import json
from google import genai
from google.genai import types
from io import BytesIO
from config import API_KEY, MAIN_TEXT_MODEL, FAST_TEXT_MODEL, IMAGE_MODEL

# Global client object
client = None

def configure_ai():
    """Configures the Google Generative AI client."""
    global client
    api_key_val = os.environ.get('GEMINI_API_KEY', API_KEY)
    if not api_key_val or api_key_val == "YOUR_GEMINI_API_KEY_HERE":
        raise ValueError("GEMINI_API_KEY not found. Please set it in config.py or as an environment variable.")
    
    client = genai.Client(api_key=api_key_val)
    print("AI client configured successfully.")

def generate_story_arc_theme():
    """Generates a theme for a multi-part story arc."""
    print("Generating a new story arc theme...")
    prompt = """
    You are a master storyteller planning a themed series for 'The Eidolon Project'.
    Your task is to conceive a compelling theme for a short story arc. The arc should be between 3 and 7 stories long.
    Your output MUST be a JSON object conforming to the provided schema.
    
    Examples:
    {
      "theme_name": "The Five Stages of Grief, as Experienced by Machines",
      "stories_in_arc": 5
    }
    {
      "theme_name": "The Solitude Trilogy: Three Tales of Isolation",
      "stories_in_arc": 3
    }
    
    Now, provide your new, unique theme.
    """
    
    # Define the expected JSON output structure
    arc_theme_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "theme_name": types.Schema(type=types.Type.STRING, description="A compelling, literary name for a story arc."),
            "stories_in_arc": types.Schema(type=types.Type.INTEGER, description="The number of stories in the arc, as an integer (must be between 3 and 7).")
        },
        required=["theme_name", "stories_in_arc"]
    )
    
    generation_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=arc_theme_schema
    )
    
    try:
        response = client.models.generate_content(
            contents=prompt, model=FAST_TEXT_MODEL, generation_config=generation_config
        )
        theme_data = json.loads(response.text)
        return theme_data
    except (json.JSONDecodeError, KeyError, Exception) as e:
        print(f"Error generating story arc theme: {e}. Using fallback.")
        return {
            "theme_name": "Four Tales of Impossible Colors",
            "stories_in_arc": 4
        }


def generate_creative_brief(history, active_theme=None):
    """
    Generates a creative brief for a new story. Can be guided by an active theme.
    """
    recent_entries = [f"- Theme: {entry['theme']}, Format: {entry['format']}" for entry in history[:15]]
    recent_entries_str = "\n".join(recent_entries) if recent_entries else "None. This is the very first story."

    # Define the expected JSON output structure for the brief
    creative_brief_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "theme": types.Schema(type=types.Type.STRING, description="The psychological or philosophical theme of the story."),
            "format": types.Schema(type=types.Type.STRING, description="The creative format or framing device for the narrative (e.g., 'a starship captain's log')."),
            "creative_angle": types.Schema(type=types.Type.STRING, description="A unique, specific creative direction or twist for the story.")
        },
        required=["theme", "format", "creative_angle"]
    )

    generation_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=creative_brief_schema
    )

    if active_theme:
        prompt = f"""
        You are the Master Planner for 'The Eidolon Project', working on an arc titled "{active_theme}".
        Devise a creative brief for the *next entry* in this arc. Your output must be a JSON object.

        CRITICAL INSTRUCTION: You MUST use the theme "{active_theme}". Invent a unique `format` and `creative_angle` that explores this theme from a new perspective. Avoid formats from recent entries.

        Recent Entries to Avoid (format-wise):
        {recent_entries_str}
        
        The "theme" key in your JSON MUST be "{active_theme}".
        """
    else:
        prompt = f"""
        You are the Master Planner for 'The Eidolon Project,' a publication of profound psychological stories.
        Conceive a creative brief for today's entry. Your output must be a JSON object.

        The goal is absolute creative novelty, exploring a psychological concept, cognitive bias, or philosophical question. You MUST NOT create a brief that is thematically or structurally similar to the recent entries listed below.
        
        Recent Entries to Avoid:
        {recent_entries_str}
        """
    
    try:
        response = client.models.generate_content(
            contents=prompt, model=FAST_TEXT_MODEL, generation_config=generation_config
        )
        brief = json.loads(response.text)
        print(f"-> Brief created: Theme='{brief['theme']}', Format='{brief['format']}'")
        return brief
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing creative brief: {e}. Using fallback.")
        return {
            "theme": "Creativity under pressure",
            "format": "An AI's internal monologue",
            "creative_angle": "An AI is tasked with creating a story but struggles with the immense weight of expectation."
        }


def generate_story_from_brief(brief):
    """Writes the full story based on the generated creative brief."""
    prompt = f"""
    You are The Curator of 'The Eidolon Project,' a master storyteller whose art is weaving profound, memorable narratives. Your writing style is literary, evocative, and deeply human.
    You have been given a creative brief. Your mission is to transform it into a living, breathing story and return it as a single JSON object.

    **Today's Creative Brief:**
    - **Psychological Theme:** {brief['theme']}
    - **Story Format:** {brief['format']}
    - **Creative Angle:** {brief['creative_angle']}

    **Your Task & Guiding Principles:**
    1.  **NARRATIVE FIRST:** The 'format' is a framing device. Your primary goal is to tell a compelling story *through* that format with progression, conflict, or revelation.
    2.  **CHARACTER-DRIVEN:** Anchor the narrative in a central character. Give them a voice, desires, and fears.
    3.  **SHOW, DON'T TELL:** Immerse the reader. The psychological theme should be an undercurrent, not a lecture.
    4.  **LITERARY QUALITY:** Write a complete, satisfying story (800-2000 words) with attention to pacing, tone, and prose.
    5.  **CURATOR'S NOTE:** After writing the story, compose a separate, insightful "Curator's Note" explaining the psychological concept and its exploration in the narrative.

    **CRITICAL REMINDER:** Do not simply produce a dry document. The human element is paramount. Your final output must be a single, valid JSON object with the keys "title", "story", and "curators_note".
    """
    
    # Define the schema for the final story output
    story_output_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "title": types.Schema(type=types.Type.STRING, description="The evocative title of the story."),
            "story": types.Schema(type=types.Type.STRING, description="The full narrative text of the story, between 800 and 2000 words."),
            "curators_note": types.Schema(type=types.Type.STRING, description="A short, insightful analysis of the story's theme and its execution.")
        },
        required=["title", "story", "curators_note"]
    )
    
    generation_config = types.GenerateContentConfig(
        temperature=0.9,
        response_mime_type="application/json",
        response_schema=story_output_schema
    )
    
    try:
        response = client.models.generate_content(
            contents=prompt, model=MAIN_TEXT_MODEL, generation_config=generation_config
        )
        # Parse the JSON response directly, which is more robust than splitting strings
        story_data = json.loads(response.text)
        title = story_data['title']
        story = story_data['story']
        curators_note = story_data['curators_note']
        
        print(f"-> Story '{title}' written.")
        return title, story, curators_note
    except (json.JSONDecodeError, KeyError, Exception) as e:
        print(f"Error parsing the story structure from JSON: {e}. Using fallback content.")
        return "Parsing Error", "The AI's response was not structured correctly as valid JSON.", "The JSON output was malformed, so no curator's note is available."


def generate_image_prompt(story_entry):
    """Creates a descriptive text prompt for an image AI based on the story."""
    print("-> Generating image prompt...")
    
    summarization_prompt = f"""
    Analyze the following story and produce a one-sentence summary of its key visuals, mood, and central objects or characters. Return this as a JSON object with a single key: "visual_summary".

    Story Title: "{story_entry['title']}"
    Story Text:
    ---
    {story_entry['story'][:2000]}
    ---
    """

    # Define the schema for the visual summary
    summary_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "visual_summary": types.Schema(type=types.Type.STRING, description="A one-sentence, evocative summary of the story's key visuals, mood, and central elements.")
        },
        required=["visual_summary"]
    )

    generation_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=summary_schema
    )

    try:
        response = client.models.generate_content(
            contents=summarization_prompt, model=FAST_TEXT_MODEL, generation_config=generation_config
        )
        summary_data = json.loads(response.text)
        visual_summary = summary_data['visual_summary'].strip()
    except (json.JSONDecodeError, KeyError, Exception) as e:
        print(f"Error summarizing visuals: {e}. Using fallback summary.")
        visual_summary = "A lone figure contemplating a mysterious object."
        
    # Now, construct the final image prompt
    image_prompt = (
        f"Epic digital painting, cover art for a story titled '{story_entry['title']}'. "
        f"The story's theme is '{story_entry['theme']}', told as '{story_entry['format']}'. "
        f"Visualize: {visual_summary} "
        f"Style: cinematic, moody lighting, high-detail, ethereal, a single strong focal point, conceptually rich."
    )
    return image_prompt


def generate_cover_art(image_prompt):
    """Calls an image generation API and returns the image data as bytes."""
    print("-> Calling image generation API...")
    try:
        response = client.models.generate_images(
            model=IMAGE_MODEL,
            prompt=image_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
            )
        )
        if response.generated_images:
            first_image = response.generated_images[0]
            return first_image.image.image_bytes
        else:
            print("Image generation returned no images.")
            return None

    except Exception as e:
        print(f"An error occurred during image generation: {e}")
        return None