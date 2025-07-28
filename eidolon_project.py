import os
import json
import datetime
import re
import sys
import markdown
from google import genai
from google.genai import types
import xml.etree.ElementTree as ET
from xml.dom import minidom
from config import MODEL_NAME, HISTORY_FILE, RSS_FILE
import urllib.parse


# --- 1. SETUP AND INITIALIZATION ---

def configure_ai():
    """Configures the Google Generative AI model."""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
        raise ValueError("GEMINI_API_KEY environment variable not found. Please set it in your GitHub Secrets. Get a key from Google AI Studio.")
    
    return  genai.Client(
        api_key=api_key
    )
    
    # genai.configure(api_key=API_KEY)
    # return genai.GenerativeModel(MODEL_NAME)

model = MODEL_NAME
client = configure_ai()

# --- 2. HISTORY MANAGEMENT ---

def load_history():
    """Loads the history of generated stories from the JSON file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_history(history):
    """Saves the updated history to the JSON file."""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

# --- 3. CORE AI GENERATION ---

def generate_creative_brief(history):
    """
    First AI call: Asks the AI to act as a planner and devise a unique
    theme and format for a new story, avoiding recent topics.
    """
    print("Stage 1/3: Generating a creative brief...")

    # Use the last 15 entries to ensure variety
    recent_entries = [f"- Theme: {entry['theme']}, Format: {entry['format']}" for entry in history[:15]]
    recent_entries_str = "\n".join(recent_entries) if recent_entries else "None. This is the very first story."

    prompt = f"""
    You are the Master Planner for 'The Eidolon Project,' a daily publication of profound psychological stories.
    Your task is to conceive a creative brief for today's entry. This brief will guide The Curator (the writer AI).

    The goal is absolute creative novelty. The story should be as inventive as a 'Black Mirror' episode and as beautiful as a force of nature.
    It must explore a psychological concept, cognitive bias, or philosophical question in a deeply human way.

    INSPIRATION (DO NOT be limited by this list; invent your own):
    - Psychological Themes: Anosognosia, Solipsism, The Dunning-Kruger Effect, The Tetris Effect, Fata Morgana, Imposter Syndrome, The Hedonic Treadmill, Cognitive Dissonance, Chronophobia (fear of time).
    - Creative Formats: A personal diary entry from a peculiar character, a series of unsent letters, a transcript of a final phone call, an excerpt from a starship captain's log, a detective's case file notes, a last will and testament with unusual clauses, an anthropologist's field notes on a bizarre modern ritual, a confession made under strange circumstances.

    FORMATTING GUIDELINES: The format should be a vessel for a compelling narrative. It must be inherently readable and engaging. Avoid formats that are primarily lists, technical documents, or bureaucratic paperwork. For example, DO NOT use formats like shopping lists, recipes, technical bug reports, legal agreements (EULAs), itemized bills, or raw computer logs. The story should flow naturally, not be confined by a rigid, non-literary structure.

    CRITICAL INSTRUCTION: To ensure variety, you MUST NOT create a brief that is thematically or structurally similar to the most recent entries listed below. Be original.

    Recent Entries to Avoid:
    {recent_entries_str}

    Now, provide your new, unique creative brief. The output MUST be a JSON object with three keys: "theme", "format", and "creative_angle".
    - "theme": The core psychological or philosophical concept.
    - "format": The specific, creative medium for the story.
    - "creative_angle": A one-sentence hook or unique perspective for The Curator to use.

    Example JSON output:
    {{
      "theme": "The Bystander Effect",
      "format": "A real-time transcript from a city's public surveillance AI",
      "creative_angle": "The AI narrator is developing a primitive form of frustration as it observes human inaction during a crisis."
    }}

    Your JSON response:
    """

    generate_content_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=types.Schema(
            type = types.Type.OBJECT,
            properties = {
                "theme": types.Schema(
                    type = types.Type.STRING,
                ),
                "format": types.Schema(
                    type = types.Type.STRING,
                ),
                "creative_angle": types.Schema(
                    type = types.Type.STRING,
                ),
            },
        ),
    )

    response = client.models.generate_content(contents=prompt, model=model, config=generate_content_config)
    try:
        # Clean up the response to ensure it's valid JSON
        json_str = response.text.strip().lstrip('```json').rstrip('```')
        brief = json.loads(json_str)
        print(f"-> Brief created: Theme='{brief['theme']}', Format='{brief['format']}'")
        return brief
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing creative brief: {e}")
        print(f"Raw response was: {response.text}")
        # Fallback to a default brief if generation fails
        return {
            "theme": "Creativity under pressure",
            "format": "An AI's internal monologue",
            "creative_angle": "An AI is tasked with creating a story but struggles with the immense weight of expectation, mirroring human artistic anxiety."
        }


def generate_story_from_brief(brief):
    """
    Second AI call: Asks the AI to act as The Curator and write the full
    story based on the generated creative brief.
    """
    print("Stage 2/3: Writing the story as The Curator...")

    prompt = f"""
    You are The Curator of 'The Eidolon Project.' Your writing is your art. It must be stunning, profound, and memorable.
    You have been given the following creative brief for today's entry. Execute it with maximum creativity and literary skill.

    **Today's Creative Brief:**
    - **Psychological Theme:** {brief['theme']}
    - **Story Format:** {brief['format']}
    - **Creative Angle:** {brief['creative_angle']}

    **Your Task:**
    1.  Write a compelling narrative based on the brief. The length should be substantial enough for a satisfying read (aim for 800-2000 words).
    2.  Show, don't tell. Let the reader experience the psychological theme through character, plot, and atmosphere rather than explaining it directly.
    3.  After the story, write a short, insightful "Curator's Note." This note should be separate from the story and briefly explain the psychological concept and how the narrative explored it.

    **Output Format (Strictly follow this structure):**
    [TITLE]: Your story's title here
    [STORY]:
    Your full story begins here.
    ...
    (The story can have multiple paragraphs)
    ...
    The story ends here.
    |||---|||
    [CURATOR'S NOTE]:
    Your analysis and reflection on the theme begin here.

    Begin. Let your creation be a mirror to the human mind.
    """

    generation_config = types.GenerateContentConfig(
        temperature=0.9 # Higher temperature for more creative, less predictable writing
    )

    response = client.models.generate_content(contents=prompt, model=model, config=generation_config)

    # Parse the structured response
    try:
        parts = response.text.split('|||---|||')
        header_part = parts[0]
        note_part = parts[1]

        title = header_part.split('[TITLE]:')[1].split('[STORY]:')[0].strip()
        story = header_part.split('[STORY]:')[1].strip()
        curators_note = note_part.split('[CURATOR\'S NOTE]:')[1].strip()

        return title, story, curators_note
    except (IndexError, AttributeError) as e:
        print(f"Error parsing the story structure: {e}")
        print(f"Raw response was: {response.text}")
        return "Parsing Error", "The AI's response was not structured correctly. Please try again.", "No note available."

# --- 4. RSS FEED GENERATION ---

def update_rss_feed(history):
    """
    Generates a correctly formatted RSS feed, using URL encoding to ensure
    direct links to the viewer.html archive work correctly.
    """
    print("Stage 3/3: Building final RSS feed with URL-encoded permanent links...")

    namespaces = {
        "atom": "http://www.w3.org/2005/Atom",
        "content": "http://purl.org/rss/1.0/modules/content/"
    }
    
    ET.register_namespace('atom', namespaces['atom'])
    ET.register_namespace('content', namespaces['content'])
    
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    base_url = "https://harrydekat.github.io/eidolon-project/"
    viewer_url = f"{base_url}viewer.html"
    
    ET.SubElement(channel, "title").text = "The Eidolon Project"
    ET.SubElement(channel, "link").text = viewer_url
    channel.append(ET.Element(ET.QName(namespaces["atom"], "link"), attrib={"href": f"{base_url}rss.xml", "rel": "self", "type": "application/rss+xml"}))
    ET.SubElement(channel, "description").text = "A daily, psychologically-rich story generated by AI."
    ET.SubElement(channel, "language").text = "en-us"
    ET.SubElement(channel, "lastBuildDate").text = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %z")

    container_style = "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333333; padding: 10px 20px; max-width: 700px; margin: auto;"
    meta_style = "font-size: 14px; font-style: italic; color: #888888; margin-bottom: 25px;"
    hr_style = "border: 0; border-top: 1px solid #dddddd; margin: 40px 0;"
    note_container_style = "background-color: #f7f7f7; border-left: 4px solid #cccccc; padding: 15px 20px; margin-top: 30px; font-size: 15px;"
    note_title_style = "font-weight: bold; color: #1a1a1a; margin: 0 0 10px 0;"
    
    cdata_replacements = {}

    for entry in history:
        item = ET.SubElement(channel, "item")
        
        encoded_date = urllib.parse.quote(entry['date'])
        story_link = f"{viewer_url}?id={encoded_date}"
        
        ET.SubElement(item, "title").text = clean_invalid_xml_chars(entry['title'])
        ET.SubElement(item, "link").text = story_link
        pub_date = datetime.datetime.fromisoformat(entry['date']).strftime("%a, %d %b %Y %H:%M:%S %z")
        ET.SubElement(item, "pubDate").text = pub_date
        ET.SubElement(item, "guid", isPermaLink="true").text = story_link

        cleaned_story = clean_invalid_xml_chars(entry['story'])
        cleaned_note = clean_invalid_xml_chars(entry['curators_note'])
        pretty_theme = entry['theme'].replace('_', ' ').title()
        pretty_format = entry['format'].replace('_', ' ').title()

        plain_text_story = strip_markdown(cleaned_story)
        plain_text_story = re.sub(r'\s+', ' ', plain_text_story).strip()
        excerpt = (plain_text_story[:250] + '...') if len(plain_text_story) > 250 else plain_text_story
        ET.SubElement(item, "description").text = f"{excerpt}\n\n[Theme: {pretty_theme}]"

        story_html = markdown.markdown(cleaned_story.strip(), extensions=['nl2br'])
        note_html = markdown.markdown(cleaned_note.strip(), extensions=['nl2br'])

        full_html_content = f"""
        <div style="{container_style}">
            <p style="{meta_style}">Theme: {pretty_theme}<br/>Format: {pretty_format}</p>
            {story_html}
            <hr style="{hr_style}" />
            <blockquote style="{note_container_style}">
                <p style="{note_title_style}">Curator's Note</p>
                {note_html}
            </blockquote>
            <hr style="border:0; border-top: 1px solid #eee; margin: 30px 0;" />
            <p style="text-align:center; font-size: 0.9em; color: #888;">
                <a href="{story_link}" style="color: #0056b3; text-decoration:none;">View this story on the web</a>
            </p>
        </div>
        """
        
        placeholder = f"__EIDOLON_CONTENT_{entry['date']}__"
        cdata_replacements[placeholder] = f"<![CDATA[{full_html_content.strip()}]]>"
        ET.SubElement(item, ET.QName(namespaces["content"], "encoded")).text = placeholder

    xml_string = ET.tostring(ET.ElementTree(rss).getroot(), encoding='unicode')

    for placeholder, real_content in cdata_replacements.items():
        xml_string = xml_string.replace(placeholder, real_content)

    pretty_xml_str = minidom.parseString(xml_string).toprettyxml(indent="  ")

    with open(RSS_FILE, 'w', encoding='utf-8') as f:
        f.write(pretty_xml_str)
    
    print("-> RSS feed successfully built with URL-encoded permanent links.")

def clean_invalid_xml_chars(text):
    """
    Removes any characters that are not valid in XML 1.0 documents.
    This prevents "not well-formed (invalid token)" errors during XML parsing.
    The valid character ranges are defined by the XML 1.0 specification.
    """
    # Regex for valid XML 1.0 characters
    # See: https://www.w3.org/TR/xml/#charsets
    # Valid ranges: #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | [#x10000-#x10FFFF]
    invalid_xml_chars_re = re.compile(
        u'[^\u0009\u000a\u000d\u0020-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]'
    )
    return invalid_xml_chars_re.sub('', text)

# eidolon_project.py (add this new function)

def strip_markdown(text):
    """A simple function to strip common markdown formatting for plain text summaries."""
    # Remove bold, italic, code ticks
    text = re.sub(r'([*_`])', '', text)
    # Remove horizontal rules
    text = re.sub(r'---', '', text)
    # Remove headers
    text = re.sub(r'#+\s', '', text)
    # Remove links, keeping the link text
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    return text

# --- 5. MAIN EXECUTION ---

def regenerate_feed_from_history():
    """Skips AI generation and rebuilds the RSS feed from the local history.json."""
    print("--- Regeneration Mode Activated ---")
    print("Reading from local history file...")
    history = load_history()
    
    if not history:
        print("Error: history.json is empty or not found. Cannot regenerate.")
        return

    # Call the existing RSS update function with the loaded history
    update_rss_feed(history)
    
    print("\n--- Success! ---")
    print(f"The RSS feed has been successfully regenerated from {len(history)} entries.")


def main():
    """Main function to run the Eidolon Project script."""

    # --- NEW: Check for the --regenerate flag ---
    if '--regenerate' in sys.argv:
        regenerate_feed_from_history()
        return # Exit the script after regenerating

    # --- Original execution path if no flag is found ---
    print("--- Initializing The Eidolon Project (New Story Mode) ---")
    
    history = load_history()
    
    brief = generate_creative_brief(history)
    
    title, story, curators_note = generate_story_from_brief(brief)
    
    new_entry = {
        "date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "title": title,
        "theme": brief['theme'],
        "format": brief['format'],
        "story": story,
        "curators_note": curators_note
    }
    
    history.insert(0, new_entry)
    
    save_history(history)
    
    update_rss_feed(history)
    
    print("\n--- Success! ---")
    print(f"A new story has been created: '{title}'")
    print("Your RSS feed is ready for you to read.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n--- An unexpected error occurred ---")
        print(e)