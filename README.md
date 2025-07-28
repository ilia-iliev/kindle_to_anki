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
- `kindle_detector.py` - Kindle device detection functionality
- `kindle_reader.py` - Kindle database reading and word extraction
- `frequent_words.py` - Frequent words downloading, caching, and filtering
- `tests/` - Test suite
- `PRD.md` - Product Requirements Document
- `last_access.txt` - Plaintext file storing the last access date
- `frequent_words.json` - JSON cache file storing frequent words

## Requirements

- Python 3.12+
- Linux system (for Kindle device detection)
- Kindle device with USB connection capability
- Internet connection (for downloading frequent words list)

## Data Storage

The application stores data in two files:
- `last_access.txt` - Plaintext file storing the last access date to track which words have been processed since the last run
- `frequent_words.json` - JSON file caching the top 1000 most frequent English words downloaded from the internet
