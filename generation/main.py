# main.py
# This is the main entry point for The Eidolon Project.

import os
import sys
import datetime
import shutil
import random

import ai_generators
import history_manager
import output_generators
import theme_manager
from config import STORIES_DIR, ART_DIR, ENABLE_IMAGE_GENERATION

def create_output_directories():
    """Creates the necessary output directories if they don't exist."""
    os.makedirs(ART_DIR, exist_ok=True)
    os.makedirs(STORIES_DIR, exist_ok=True)

def regenerate_all_outputs():
    """Skips AI generation and rebuilds all output files from history.json."""
    print("--- Regeneration Mode Activated ---")
    history = history_manager.load_history()

    if not history:
        print("Error: history.json is empty or not found. Cannot regenerate.")
        return

    print(f"Loaded {len(history)} entries from history.")
    
    # 1. Wipe the stories directory for a clean slate
    print(f"Wiping contents of '{STORIES_DIR}'...")
    if os.path.exists(STORIES_DIR):
        shutil.rmtree(STORIES_DIR)
    create_output_directories()
    
    # 2. Re-create all Markdown files from history
    print("Recreating all Markdown files...")
    for entry in history:
        # The art path is stored in the entry, if it exists
        art_filename = entry.get("cover_art_path") # e.g., "art/2024-....png"
        output_generators.save_story_as_markdown(entry, art_filename)
    print(f"Successfully recreated {len(history)} Markdown files.")

    # 3. Rebuild the RSS feed
    print("Rebuilding RSS feed...")
    output_generators.update_rss_feed(history)
    print("RSS feed rebuilt.")
    
    print("\n--- Success! All outputs have been regenerated. ---")


def run_new_story_generation():
    """Handles the full process of generating a new story."""
    print("--- Initializing The Eidolon Project (New Story Mode) ---")
    
    history = history_manager.load_history()
    total_stages = 4 if ENABLE_IMAGE_GENERATION else 3
    
    # 1. Theme Management
    active_theme_state = theme_manager.get_active_theme()
    current_theme = None
    if active_theme_state:
        current_theme = active_theme_state["theme_name"]
        print(f"Continuing story arc: '{current_theme}' ({active_theme_state['stories_completed'] + 1}/{active_theme_state['stories_in_arc']})")
    elif random.randint(1, 5) == 1: # 1 in 5 chance to start a new theme
        print("Decided to start a new story arc!")
        active_theme_state = theme_manager.start_new_theme()
        if active_theme_state:
             current_theme = active_theme_state["theme_name"]
             print(f"Generated new story arc: '{current_theme}' ({active_theme_state['stories_completed'] + 1}/{active_theme_state['stories_in_arc']})")

    # 2. AI Story Generation
    print(f"Stage 1/{total_stages}: Generating a creative brief...")
    brief = ai_generators.generate_creative_brief(history, active_theme=current_theme)
    
    print(f"Stage 2/{total_stages}: Writing the story as The Curator...")
    title, story, curators_note = ai_generators.generate_story_from_brief(brief)
    
    # 3. Create Story Entry
    date_now = datetime.datetime.now(datetime.timezone.utc)
    new_entry = {
        "date": date_now.isoformat(),
        "title": title,
        "theme": brief['theme'],
        "format": brief['format'],
        "story": story,
        "curators_note": curators_note,
        "cover_art_path": None # Placeholder
    }
    
    # 4. AI Cover Art Generation
    if ENABLE_IMAGE_GENERATION:
        print(f"Stage 3/{total_stages}: Generating Cover Art...")
        try:
            image_prompt = ai_generators.generate_image_prompt(new_entry)
            print(f"-> Image Prompt: {image_prompt}")
            image_bytes = ai_generators.generate_cover_art(image_prompt)
            
            if image_bytes:
                art_filename = f"{date_now.isoformat().replace(':', '-')}.png"
                art_filepath = os.path.join(ART_DIR, art_filename)
                with open(art_filepath, "wb") as f:
                    f.write(image_bytes)
                
                # Store relative path for portability
                relative_art_path = os.path.join(os.path.basename(ART_DIR), art_filename).replace("\\", "/")
                new_entry["cover_art_path"] = relative_art_path
                print(f"-> Cover art saved to '{art_filepath}'")
            else:
                print("-> Cover art generation failed. Skipping.")

        except Exception as e:
            print(f"An error occurred during cover art generation: {e}")
            print("Continuing without cover art.")
    else:
        print("Skipping Stage 3: Cover Art generation is disabled in config.py.")


    # 5. Save Outputs
    print(f"Stage {total_stages}/{total_stages}: Saving outputs...")

    # Save individual Markdown file
    output_generators.save_story_as_markdown(new_entry, new_entry["cover_art_path"])
    print(f"-> Saved story to Markdown file.")

    # Update and save history
    history.insert(0, new_entry)
    history_manager.save_history(history)
    print(f"-> History file updated.")
    
    # Update theme progress
    if active_theme_state:
        theme_manager.update_theme_progress()

    # Update RSS feed
    output_generators.update_rss_feed(history)
    print(f"-> RSS feed updated.")
    
    print("\n--- Success! ---")
    print(f"A new story has been created: '{title}'")
    print("Your outputs are ready for you to view.")


def main():
    """Main function to run the Eidolon Project script."""
    try:
        create_output_directories()
        
        # Check for the --regenerate flag
        if '--regenerate' in sys.argv:
            regenerate_all_outputs()
        else:
            ai_generators.configure_ai()
            run_new_story_generation()
            
    except Exception as e:
        print(f"\n--- An unexpected error occurred in main execution ---")
        print(e)
        # Add more detailed error logging here if needed
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()