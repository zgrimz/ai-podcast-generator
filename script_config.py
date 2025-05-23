# script_config.py

# --- General Application Configuration ---
INPUT_ARTICLES_FOLDER = "input_articles"
OUTPUT_PODCAST_FOLDER = "output_podcasts"
TEMP_AUDIO_FOLDER = "temp_audio_files"
PROMPT_FILE = "prompt.txt"

# --- Anthropic Configuration ---
ANTHROPIC_MODEL_NAME = "claude-3-7-sonnet-20250219"
ANTHROPIC_MAX_TOKENS = 8192
ANTHROPIC_TEMPERATURE = 0.7

# --- Speechify Configuration ---
SPEECHIFY_API_URL = "https://api.sws.speechify.com/v1/audio/speech"
SPEECHIFY_VOICE_ID = "kristy"
SPEECHIFY_TTS_MODEL = "simba-english"
SPEECHIFY_EMOTION = "assertive"
SPEECHIFY_PITCH = 0
SPEECHIFY_SPEED = 1.0
SPEECHIFY_TEXT_NORMALIZATION = True
SPEECHIFY_AUDIO_FORMAT = "mp3"
SPEECHIFY_MAX_CHARS_PER_REQUEST = 2000
SPEECHIFY_REQUEST_TIMEOUT_SECONDS = 90
SPEECHIFY_INTER_CHUNK_DELAY_SECONDS = 1.5