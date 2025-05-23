# api_clients.py
import os
import base64
import json
import time
import requests
import re # For JSON extraction fallback
from dotenv import load_dotenv
from anthropic import Anthropic
from pydub import AudioSegment
from pydub.exceptions import CouldntEncodeError

import script_config # Import configurations

# Load environment variables from .env file (for API Keys)
load_dotenv()

# --- API Key Retrieval ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SPEECHIFY_API_KEY = os.getenv("SPEECHIFY_API_KEY")

# --- Anthropic Client ---
class ClaudeAPI:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found. Please set it in your .env file.")
        self.client = Anthropic(api_key=api_key)
        self.model_name = script_config.ANTHROPIC_MODEL_NAME
        self.max_tokens = script_config.ANTHROPIC_MAX_TOKENS
        self.temperature = script_config.ANTHROPIC_TEMPERATURE

    def generate_script(self, prompt_template, articles_text):
        print(f"Generating podcast script with Claude ({self.model_name})...")
        prompt = prompt_template.format(articles_text=articles_text)

        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = response.content[0].text
            cleaned_response_text = response_text.strip()

            if "```json" in cleaned_response_text:
                start_idx = cleaned_response_text.find("```json") + 7
                end_idx = cleaned_response_text.rfind("```")
                if start_idx > 6 and end_idx > start_idx:
                    cleaned_response_text = cleaned_response_text[start_idx:end_idx].strip()
            elif "```" in cleaned_response_text:
                cleaned_response_text = cleaned_response_text.replace("```", "").strip()

            script_json = json.loads(cleaned_response_text)
            print("Podcast script generated successfully.")
            return script_json
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from Claude response: {e}")
            print(f"Claude Raw Response Text (first 500 chars):\n{response_text[:500]}")
            try:
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    script_json = json.loads(json_match.group())
                    print("Successfully extracted JSON from response using regex fallback.")
                    return script_json
                else:
                    print("Regex fallback could not find a JSON object.")
            except Exception as inner_e:
                print(f"Regex fallback for JSON extraction also failed: {inner_e}")
            return None
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return None

# --- Speechify Client ---
class SpeechifyAPI:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("SPEECHIFY_API_KEY not found. Please set it in your .env file.")

        self.api_key = api_key
        # Parameters are now directly from script_config
        self.voice_id = script_config.SPEECHIFY_VOICE_ID
        self.api_url = script_config.SPEECHIFY_API_URL
        self.tts_model = script_config.SPEECHIFY_TTS_MODEL
        self.emotion = script_config.SPEECHIFY_EMOTION
        self.pitch = script_config.SPEECHIFY_PITCH
        self.speed = script_config.SPEECHIFY_SPEED
        self.text_normalization = script_config.SPEECHIFY_TEXT_NORMALIZATION
        self.audio_format = script_config.SPEECHIFY_AUDIO_FORMAT
        self.max_chars = script_config.SPEECHIFY_MAX_CHARS_PER_REQUEST
        self.timeout = script_config.SPEECHIFY_REQUEST_TIMEOUT_SECONDS
        self.delay_between_chunks = script_config.SPEECHIFY_INTER_CHUNK_DELAY_SECONDS
        self.temp_audio_folder = script_config.TEMP_AUDIO_FOLDER

        if not self.voice_id:
            raise ValueError("SPEECHIFY_VOICE_ID not found in script_config.py.")
        if not self.api_url:
            raise ValueError("SPEECHIFY_API_URL not found in script_config.py.")


    def text_to_speech(self, text_content, output_filename_base, segment_index):
        audio_segments_paths = []
        text_preview = "".join(c if c.isalnum() else "_" for c in text_content[:30])

        text_chunks = []
        if len(text_content) > self.max_chars:
            print(f"Segment '{text_preview}...' is > {self.max_chars} chars. Chunking...")
            start = 0
            while start < len(text_content):
                end = start + self.max_chars
                if end < len(text_content): # Try to split at a sentence end
                    period_index = text_content.rfind('.', start, end)
                    if period_index != -1 and period_index > start:
                        end = period_index + 1
                text_chunks.append(text_content[start:end])
                start = end
        else:
            text_chunks.append(text_content)

        for i, chunk in enumerate(text_chunks):
            if not chunk.strip():
                print(f"Skipping empty chunk for {output_filename_base}, segment {segment_index}")
                continue

            chunk_filename = os.path.join(self.temp_audio_folder, f"{output_filename_base}_seg{segment_index}_chunk{i}.{self.audio_format}")
            print(f"Requesting audio for: {output_filename_base} (seg {segment_index}, chunk {i}, {len(chunk)} chars): '{chunk[:40].strip().replace(os.linesep, ' ')}...'")

            payload = {
                "input": chunk, "voice_id": self.voice_id, "model": self.tts_model,
                "emotion": self.emotion, "pitch": self.pitch, "speed": self.speed,
                "text_normalization": self.text_normalization, "audio_format": self.audio_format
            }
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

            try:
                response = requests.post(self.api_url, json=payload, headers=headers, timeout=self.timeout)

                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '').lower()
                    if 'application/json' in content_type:
                        try:
                            response_json = response.json()
                            if "audio_data" in response_json:
                                binary_audio_data = base64.b64decode(response_json["audio_data"])
                                with open(chunk_filename, 'wb') as f: f.write(binary_audio_data)
                                file_size = os.path.getsize(chunk_filename)
                                if file_size < 100: print(f"WARNING: Small file {chunk_filename} ({file_size} bytes).")
                                audio_segments_paths.append(chunk_filename)
                                print(f"Audio chunk from JSON saved: {chunk_filename} ({file_size} bytes)")
                            else:
                                print(f"ERROR: Speechify JSON OK but no 'audio_data'. Resp: {response.text[:200]}")
                                continue
                        except (json.JSONDecodeError, base64.binascii.Error, Exception) as e:
                            print(f"ERROR: Processing Speechify JSON/Base64 OK response failed: {e}. Resp: {response.text[:200]}")
                            continue
                    elif f'audio/{self.audio_format}' in content_type or ('audio/mpeg' in content_type and self.audio_format == 'mp3'):
                        with open(chunk_filename, 'wb') as f: f.write(response.content)
                        file_size = os.path.getsize(chunk_filename)
                        audio_segments_paths.append(chunk_filename)
                        print(f"Direct audio chunk saved: {chunk_filename} ({file_size} bytes)")
                    else:
                        print(f"ERROR: Speechify OK but unexpected Content-Type: {content_type}. Resp: {response.text[:200]}")
                        continue
                else:
                    print(f"ERROR: Speechify API non-200 status: {response.status_code}.")
                    try: print(f"Speechify Error Details (JSON): {response.json()}")
                    except json.JSONDecodeError: print(f"Speechify Error Response (text): {response.text[:500]}")
                    continue

                time.sleep(self.delay_between_chunks)

            except requests.exceptions.RequestException as e:
                print(f"Speechify Request error (chunk {i}, {output_filename_base}): {e}")
                continue
            except Exception as e:
                print(f"Unexpected error with Speechify (chunk {i}, {output_filename_base}): {e}")
                continue

        if not audio_segments_paths: return None

        if len(audio_segments_paths) > 1:
            combined = AudioSegment.empty()
            for path in audio_segments_paths:
                try:
                    combined += AudioSegment.from_file(path, format=self.audio_format)
                except Exception as e:
                    print(f"Error loading chunk {path} for stitching: {e}")
                    if hasattr(e, 'output') and e.output: print(f"FFmpeg output: {e.output.decode(errors='ignore') if isinstance(e.output, bytes) else e.output}")
                    continue

            final_path = os.path.join(self.temp_audio_folder, f"{output_filename_base}_seg{segment_index}_combined.{self.audio_format}")
            try:
                if len(combined) > 0:
                    combined.export(final_path, format=self.audio_format)
                    print(f"Combined segment saved: {final_path}")
                    for p in audio_segments_paths:
                        try: os.remove(p)
                        except OSError: pass # Clean up individual chunks
                    return final_path
                return None
            except (CouldntEncodeError, Exception) as e:
                print(f"Error exporting/combining segment {final_path}: {e}")
                return None
        elif audio_segments_paths: # Single chunk, verify and return
            try:
                AudioSegment.from_file(audio_segments_paths[0], format=self.audio_format) # Verify
                return audio_segments_paths[0]
            except Exception as e:
                print(f"Error verifying single audio chunk {audio_segments_paths[0]}: {e}")
                if hasattr(e, 'output') and e.output: print(f"FFmpeg output: {e.output.decode(errors='ignore') if isinstance(e.output, bytes) else e.output}")
                try: os.remove(audio_segments_paths[0]) # Clean invalid chunk
                except OSError: pass
                return None
        return None

# --- Instantiate Clients for Easy Import ---
claude_client = None
speechify_client = None

if ANTHROPIC_API_KEY:
    try:
        claude_client = ClaudeAPI(api_key=ANTHROPIC_API_KEY)
    except ValueError as e:
        print(f"Failed to initialize Claude client: {e}")
else:
    print("Warning: ANTHROPIC_API_KEY not found in .env. Claude client not initialized.")

if SPEECHIFY_API_KEY:
    try:
        speechify_client = SpeechifyAPI(api_key=SPEECHIFY_API_KEY)
    except ValueError as e:
         print(f"Failed to initialize Speechify client: {e}")
else:
    print("Warning: SPEECHIFY_API_KEY not found in .env. Speechify client not initialized.")