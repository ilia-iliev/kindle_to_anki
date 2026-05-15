# Kindle to Anki

Application that reads user highlights (tap and hold on words) on Kindle. These are probable unknown words and the application prepares them into AnkiDroid-importable format.

## Installation

This project uses `uv` for dependency management and Python virtual environments.

1. Clone the repository
2. Install dependencies:
   ```bash
   uv sync
   ```

## How it Works

The application will:
1. Check if a Kindle device is attached and accessible
2. Read the Kindle vocabulary database to extract looked-up words
3. Filter out common words (like 'the', 'be', 'to', 'of', 'and', etc.) from the results
4. Return words that have been looked up since the last run 
5. Create .csv files with word definitions, ready for anki import

## Development

### Running Tests
```bash
uv run pytest tests/ -v
```

### Project Structure
- `main.py` - Main application entry point with command line argument parsing
- `kindle/detector.py` - Kindle device detection functionality
- `kindle/reader.py` - Kindle database reading and word extraction
- `dictionary_service.py` - dictionaryapi.dev client with rate limiting and retries
- `csv_exporter.py` - Writes word/definition pairs to a semicolon-CSV
- `frequent_words.py` - Frequent words downloading, caching, and filtering
- `errors.py` - Shared exception classes
- `tests/` - Test suite
- `PRD.md` - Product Requirements Document

## Requirements

- Python 3.12+
- Linux system (for Kindle device detection)
- Kindle device with USB connection capability
- Internet connection (for downloading frequent words list)

## Data Storage

The application stores state under platform-specific user directories (via `platformdirs`):
- `last_access.txt` - in the user data dir (e.g. `~/.local/share/kindle-to-anki/` on Linux). Tracks which words have been processed since the last run.
- `frequent_words.json` - in the user cache dir (e.g. `~/.cache/kindle-to-anki/` on Linux). Caches the top 1000 most frequent English words.
- `words.csv` - written to the current directory by default, or to `--output-dir` if provided.
