# AI News Podcast Generator

## Overview

This Python application transforms written news articles into professional-sounding podcast episodes. It uses Claude AI to create natural, conversational scripts from your articles, then converts them to speech using Speechify's TTS API, producing a complete MP3 podcast file.

## Features

- **Intelligent Script Generation**: Uses Claude AI to synthesize multiple articles into cohesive podcast scripts
- **Natural Speech Synthesis**: Converts scripts to speech using Speechify's advanced TTS
- **Automatic Segmentation**: Processes intro, multiple stories, and outro segments
- **Smart Chunking**: Handles long text by automatically splitting at natural breakpoints
- **Flexible Configuration**: Easily customize voice, emotion, speed, and other parameters
- **Error Handling**: Robust error handling and logging throughout the pipeline

## Prerequisites

- Python 3.7+
- FFmpeg (for audio processing)
- Anthropic API key
- Speechify API key

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd news-podcast-generator
   ```

2. **Install required Python packages**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg**
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt-get install ffmpeg`
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

4. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   SPEECHIFY_API_KEY=your_speechify_api_key_here
   ```

## Configuration

Edit `script_config.py` to customize:

### Folder Structure
- `INPUT_ARTICLES_FOLDER`: Where to place your news articles (default: "input_articles")
- `OUTPUT_PODCAST_FOLDER`: Where generated podcasts are saved (default: "output_podcasts")
- `TEMP_AUDIO_FOLDER`: Temporary audio file storage (default: "temp_audio_files")

### Claude AI Settings
- `ANTHROPIC_MODEL_NAME`: Claude model to use (default: "claude-3-7-sonnet-20250219")
- `ANTHROPIC_MAX_TOKENS`: Maximum response length (default: 8192)
- `ANTHROPIC_TEMPERATURE`: Creativity level 0-1 (default: 0.7)

### Speechify TTS Settings
- `SPEECHIFY_VOICE_ID`: Voice selection (default: "kristy")
- `SPEECHIFY_EMOTION`: Speaking style (default: "assertive")
- `SPEECHIFY_SPEED`: Playback speed (default: 1.0)
- `SPEECHIFY_PITCH`: Voice pitch adjustment (default: 0)

## Usage

1. **Prepare your articles**
   - Place `.txt` files containing news articles in the `input_articles` folder
   - Each file should contain one or more related articles

2. **Run the script**
   ```bash
   python script.py
   ```

3. **Find your podcast**
   - The generated podcast will be in `output_podcasts/`
   - Filename format: `YYYY-MM-DD Episode_Title.mp3`

## Project Structure

```
news-podcast-generator/
├── script.py              # Main execution script
├── api_clients.py         # API client implementations
├── script_config.py       # Configuration settings
├── prompt.txt             # Podcast generation prompt template
├── .env                   # API keys (create this file)
├── requirements.txt       # Python dependencies
├── input_articles/        # Place news articles here
├── output_podcasts/       # Generated podcasts saved here
└── temp_audio_files/      # Temporary audio segments (auto-cleaned)
```

## How It Works

1. **Article Collection**: Reads all `.txt` files from the input folder
2. **Script Generation**: Claude AI processes articles using the prompt template to create a structured podcast script
3. **Text-to-Speech**: Each script segment is converted to audio using Speechify
4. **Audio Processing**: Individual segments are stitched together into a complete podcast
5. **Cleanup**: Temporary files are automatically removed

## Customizing the Prompt

Edit `prompt.txt` to change how podcasts are generated:
- Adjust word counts for intro/outro/stories
- Modify the writing style and tone
- Change story selection criteria
- Add custom formatting requirements

## Troubleshooting

### Common Issues

**"No module named 'pydub'"**
```bash
pip install pydub
```

**"FFmpeg not found"**
- Ensure FFmpeg is installed and in your system PATH
- Test with: `ffmpeg -version`

**"API key not found"**
- Check your `.env` file exists and contains valid API keys
- Ensure no extra spaces around the keys

**Audio segments not stitching**
- Verify FFmpeg is properly installed
- Check temp audio files are being generated
- Look for error messages about specific segments

### Debug Mode

For detailed logging, you can modify the scripts to increase verbosity or add print statements at key processing points.

## API Documentation

- [Anthropic Claude API](https://docs.anthropic.com/)
- [Speechify API](https://docs.sws.speechify.com/)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Anthropic for Claude AI
- Speechify for TTS capabilities
- The Python community for libraries