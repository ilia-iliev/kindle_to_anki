# Kindle to Anki

Application that reads user highlights (tap and hold on words) on Kindle. These are probable unknown words and the application prepares them into AnkiDroid-importable format.

## Features

### 1. Reading of probable unknown words
- **1.1** On trigger, the application detects if a kindle is attached and readable. If not attached, show helpful message.
- **1.2** After verification, open the correct database file with word lookups. The lookup words since last open are returned.

### 2. Filter out words
- **2.1** Filter obvious user miclicks (words like 'the', 'they', etc... everything in the top 1000 words in the english language)

### 3. Filter out words *(Coming soon)*
- **3.1** Filter everything in the existing anki list

## Installation

This project uses `uv` for dependency management and Python virtual environments.

1. Clone the repository
2. Install dependencies:
   ```bash
   uv sync
   ```

## Usage

### Normal Mode
Run the application to get words since last access:
```bash
uv run python main.py
```

### Test Mode
Run the application in test mode to get random 10 words:
```bash
uv run python main.py --test
```

### Help
View available command line options:
```bash
uv run python main.py --help
```

## How it Works

The application will:
1. Check if a Kindle device is attached and accessible
2. Display helpful messages if the device is not found or not readable
3. Read the Kindle vocabulary database to extract looked-up words
4. Download and cache the top 1000 most frequent English words from the internet
5. Filter out common words (like 'the', 'be', 'to', 'of', 'and', etc.) from the results
6. Store the last access date in `last_access.txt` for tracking
7. Return words that have been looked up since the last run (with frequent words filtered out)
8. Print the list of words (in normal mode) or random test words (in test mode)

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
- `frequent_words.json` - JSON file caching the top 1000 most frequent English words downloaded from the internet (cached for 30 days)

## Frequent Words Filtering

The application automatically filters out common English words that are likely accidental clicks rather than genuine vocabulary lookups. This includes:
- Articles: the, a, an
- Common verbs: be, to, of, and, in, that, have, it, for, not, on, with, he, as, you, do, at, this, but, his, by, from, they, we, say, her, she, or, an, will, my, one, all, would, there, their, what, so, up, out, if, about, who, get, which, go, me, when, make, can, like, time, no, just, him, know, take, people, into, year, your, good, some, could, them, see, other, than, then, now, look, only, come, its, over, think, also, back, after, use, two, how, our, work, first, well, way, even, new, want, because, any, these, give, day, most, us
- And many more common words...

This filtering helps focus on genuinely useful vocabulary words for Anki study. 