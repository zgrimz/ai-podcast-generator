# script.py
import os
import glob
import json
import datetime
from pydub import AudioSegment
from pydub.exceptions import CouldntEncodeError

# Import configurations and initialized API clients
import script_config # For folder paths, prompt file name etc.
from api_clients import claude_client, speechify_client # Pre-initialized instances

# --- Configuration (from script_config module) ---
INPUT_ARTICLES_FOLDER = script_config.INPUT_ARTICLES_FOLDER
OUTPUT_PODCAST_FOLDER = script_config.OUTPUT_PODCAST_FOLDER
TEMP_AUDIO_FOLDER = script_config.TEMP_AUDIO_FOLDER
PROMPT_FILE = script_config.PROMPT_FILE

# --- Helper Functions ---
def load_prompt_template():
    """Load the prompt template from file."""
    try:
        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Prompt file '{PROMPT_FILE}' not found.")
        raise
    except Exception as e:
        print(f"Error reading prompt file: {e}")
        raise

LLM_PROMPT_TEMPLATE = load_prompt_template()

def setup_folders():
    """Creates necessary folders if they don't exist."""
    for folder in [INPUT_ARTICLES_FOLDER, OUTPUT_PODCAST_FOLDER, TEMP_AUDIO_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Created folder: {folder}")

def read_articles(folder_path):
    """Reads all .txt files from a folder and concatenates their content."""
    all_text = []
    txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
    if not txt_files:
        print(f"No .txt files found in {folder_path}")
        return None
    for filepath in txt_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            all_text.append(f.read())
    print(f"Read {len(all_text)} articles.")
    return "\n\n---\n\n".join(all_text)

def stitch_audio_files(audio_file_paths, output_podcast_path):
    """Stitches multiple audio files into one MP3."""
    print(f"\nStitching final podcast from {len(audio_file_paths)} audio segments...")
    combined_audio = AudioSegment.empty()
    
    segment_format = speechify_client.audio_format if speechify_client else "mp3"

    for filepath in audio_file_paths:
        if filepath and os.path.exists(filepath):
            try:
                segment = AudioSegment.from_file(filepath, format=segment_format)
                combined_audio += segment
            except Exception as e:
                print(f"Error loading audio segment {filepath} (format: {segment_format}): {e}. Skipping.")
        else:
            print(f"Audio segment not found or invalid: {filepath}. Skipping.")
            
    if len(combined_audio) == 0:
        print("No audio data to stitch. Final podcast not created.")
        return False

    try:
        combined_audio.export(output_podcast_path, format="mp3", bitrate="192k")
        print(f"Final podcast saved: {output_podcast_path}")
        return True
    except CouldntEncodeError as e:
        print(f"Pydub Error: Could not export final MP3. {e}. Ensure FFmpeg is in PATH.")
        return False
    except Exception as e:
        print(f"Error exporting final podcast: {e}")
        return False

def cleanup_temp_files():
    """Removes temporary audio files."""
    print("Cleaning up temporary audio files...")
    audio_ext = speechify_client.audio_format if speechify_client else "mp3"
    for filepath in glob.glob(os.path.join(TEMP_AUDIO_FOLDER, f"*.{audio_ext}")):
        try:
            os.remove(filepath)
        except Exception as e:
            print(f"Could not remove temp file {filepath}: {e}")
    print("Temporary files cleanup complete.")

# --- Main Execution ---
if __name__ == "__main__":
    setup_folders()

    if not claude_client:
        print("Claude API client failed to initialize. Check .env for ANTHROPIC_API_KEY and logs. Exiting.")
        exit(1)
    if not speechify_client:
        print("Speechify API client failed to initialize. Check .env for SPEECHIFY_API_KEY, script_config.py settings, and logs. Exiting.")
        exit(1)

    articles = read_articles(INPUT_ARTICLES_FOLDER)
    if not articles:
        print("No articles to process. Exiting.")
        exit()

    podcast_script_json = claude_client.generate_script(LLM_PROMPT_TEMPLATE, articles)
    
    if not podcast_script_json or "episode_title" not in podcast_script_json:
        print("Failed to generate or parse podcast script from LLM. Exiting.")
        exit(1)

    episode_title_raw = podcast_script_json.get("episode_title", "Untitled_Podcast")
    episode_title = "".join(c for c in episode_title_raw if c.isalnum() or c in " _-").strip()
    if not episode_title: episode_title = "Untitled_Podcast"
    
    all_audio_segments_paths = []
    
    script_sections_order = ["intro"]
    story_keys = sorted([key for key in podcast_script_json if key.startswith("story_")])
    script_sections_order.extend(story_keys)
    script_sections_order.append("outro")

    segment_counter = 0
    for section_key in script_sections_order:
        section_text = podcast_script_json.get(section_key)
        if isinstance(section_text, str) and section_text.strip():
            print(f"\nProcessing TTS for section: {section_key}")
            audio_path = speechify_client.text_to_speech(section_text, section_key, segment_counter)
            if audio_path:
                all_audio_segments_paths.append(audio_path)
            else:
                print(f"Failed to generate audio for section: {section_key}.")
            segment_counter += 1
        else:
            print(f"Skipping section '{section_key}': No text content found or invalid type.")

    if not all_audio_segments_paths:
        print("No audio segments were successfully generated. Cannot create podcast. Exiting.")
        cleanup_temp_files()
        exit(1)

    today_date = datetime.date.today().strftime("%Y-%m-%d")
    final_podcast_filename = f"{today_date} {episode_title}.mp3"
    final_podcast_filepath = os.path.join(OUTPUT_PODCAST_FOLDER, final_podcast_filename)

    if stitch_audio_files(all_audio_segments_paths, final_podcast_filepath):
        print(f"\nPodcast '{final_podcast_filename}' successfully created in '{OUTPUT_PODCAST_FOLDER}'.")
    else:
        print(f"\nFailed to create podcast '{final_podcast_filename}'.")
    
    cleanup_temp_files()
    print("\n--- Script Finished ---")