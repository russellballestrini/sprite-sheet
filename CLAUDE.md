# Sprite Sheet Corpus Documentation

## Overview

This repository contains a curated corpus of public domain sprite sheets for training and testing sprite sheet processing algorithms, machine learning models, and game development tools.

**Target Size:** ~3,000 sprite sheets
**License:** CC0-1.0 (Public Domain)
**Source:** Hugging Face OpenGameArt-CC0 dataset
**Last Updated:** 2025-11-12

## Directory Structure

```
corpus/
├── raw/              # All downloaded sprite sheets (original files)
├── metadata/         # JSON metadata for each sprite sheet
├── train/            # Symlinks to training set (80% of corpus)
├── test/             # Symlinks to test set (20% of corpus)
└── README.md         # This file
```

## Data Sources

### Primary Source: Hugging Face OpenGameArt-CC0

The primary source for this corpus is the [OpenGameArt-CC0 dataset](https://huggingface.co/datasets/nyuuzyou/OpenGameArt-CC0) hosted on Hugging Face.

**Dataset Details:**
- **Total Assets:** 15,700 rows across all categories
- **2D Art Assets:** 7,300 rows (our focus)
- **License:** CC0-1.0 (Creative Commons Zero - Public Domain)
- **Format:** Parquet files with rich metadata
- **Content Types:** Sprite sheets, tilesets, character animations, UI elements, etc.

**Why This Source?**
- ✅ Legally public domain (CC0-1.0)
- ✅ Well-organized with metadata
- ✅ Large collection of game art
- ✅ Includes sprite sheets, animations, and tilesets
- ✅ Easy to download via Hugging Face datasets API
- ✅ Attribution information preserved

### Additional Sources (Future)

**Kenney.nl**
- URL: https://kenney.nl/assets
- License: CC0
- Content: 60,000+ high-quality game assets
- Note: Individual packs are free; all-in-1 bundle requires purchase ($19.95)
- Status: Planned for future inclusion

**itch.io Free Game Assets**
- URL: https://itch.io/game-assets/free
- License: Various (filter for public domain/CC0)
- Content: Community-contributed sprite sheets and game assets
- Status: Considered for future inclusion

## Sprite Sheet Selection Criteria

The fetcher script (`fetch_sprites.py`) filters for assets that are likely sprite sheets based on:

1. **Title keywords:** sprite, spritesheet, animation, character, walk, run, idle, attack, etc.
2. **Description keywords:** Similar keywords in the description field
3. **Tags:** Relevant tags indicating sprite sheets or animations
4. **File formats:** PNG, GIF, JPG, JPEG image files

## Metadata Schema

Each sprite sheet has an associated JSON metadata file in `corpus/metadata/`. The metadata includes:

```json
{
  "id": "unique_hash_id",
  "source": "OpenGameArt-CC0",
  "url": "https://opengameart.org/content/...",
  "title": "Sprite Sheet Title",
  "author": "Artist Name",
  "author_url": "https://opengameart.org/users/...",
  "post_date": "Date",
  "license": "CC0-1.0",
  "tags": ["sprite", "animation", "character"],
  "description": "Description of the sprite sheet...",
  "file_url": "Direct URL to the file",
  "file_name": "original_filename.png",
  "local_path": "corpus/raw/unique_hash_id.png"
}
```

## Training/Test Split

The corpus is split into training and test sets using the `split_corpus.py` script:

- **Training Set:** 80% of sprites (symlinked in `corpus/train/`)
- **Test Set:** 20% of sprites (symlinked in `corpus/test/`)
- **Random Seed:** 42 (for reproducibility)
- **Manifest Files:** Each split has a `manifest.json` listing all sprites

### Why Symlinks?

Symlinks are used instead of copying files to:
- Save disk space
- Maintain a single source of truth in `corpus/raw/`
- Allow easy reorganization without duplicating data

## Usage

### Fetching Sprite Sheets

```bash
# Install dependencies
pip install -r requirements.txt

# Fetch sprite sheets (default: 3000 target)
python3 fetch_sprites.py

# Fetch with custom target
python3 fetch_sprites.py --target 5000

# Test with a small sample
python3 fetch_sprites.py --target 10 --max-items 50
```

### Creating Train/Test Split

```bash
# Split corpus with default 80/20 ratio
python3 split_corpus.py

# Custom split ratio (e.g., 90/10)
python3 split_corpus.py --train-ratio 0.9

# Use different random seed
python3 split_corpus.py --seed 123
```

### Accessing the Data

**Training Set:**
```python
import json
from pathlib import Path

# Load training manifest
with open('corpus/train/manifest.json') as f:
    train_manifest = json.load(f)

# Iterate over training sprites
for sprite in train_manifest['sprites']:
    sprite_id = sprite['id']
    # Load the image from corpus/train/{sprite_id}.png
    print(f"Processing {sprite['title']} by {sprite['author']}")
```

**Test Set:**
```python
# Load test manifest
with open('corpus/test/manifest.json') as f:
    test_manifest = json.load(f)

# Access test sprites similarly
```

## Statistics

After fetching is complete, you can view statistics in the summary output:

```
Total downloaded: ~3000
Training set: ~2400 (80%)
Test set: ~600 (20%)
```

## License and Attribution

All sprite sheets in this corpus are licensed under **CC0-1.0 (Creative Commons Zero)**, which means they are effectively public domain and can be used for any purpose without attribution.

However, we **strongly encourage** providing attribution to the original artists as a matter of courtesy. All attribution information is preserved in the metadata files.

### Example Attribution

```
Sprite: "16x16 RPG Character Set"
Author: Artist Name
Source: OpenGameArt.org
License: CC0-1.0
URL: [original URL from metadata]
```

## Scripts

### `fetch_sprites.py`

Main script for downloading sprite sheets from various sources.

**Features:**
- Downloads from Hugging Face OpenGameArt-CC0 dataset
- Filters for sprite sheets automatically
- Generates unique IDs for each sprite
- Saves rich metadata in JSON format
- Skips already-downloaded files
- Rate limiting to respect servers
- Progress tracking

**Usage:**
```bash
python3 fetch_sprites.py --help
```

### `split_corpus.py`

Script for splitting the corpus into training and test sets.

**Features:**
- Configurable train/test ratio
- Reproducible splits with random seed
- Creates symlinks (saves space)
- Generates manifest files for each split
- Validates metadata before splitting

**Usage:**
```bash
python3 split_corpus.py --help
```

## Data Quality

### Inclusion Criteria

✅ **Included:**
- Sprite sheets with character animations
- Tilesets for game levels
- UI element sprites
- Animated effects and particles
- Icon sets that are sprite-like
- Any 2D game art that fits sprite sheet patterns

❌ **Excluded:**
- 3D models and assets
- Audio files (music, sound effects)
- Concept art without sprites
- Documents and text files
- Non-image formats

### Known Issues

Some items may fail to download due to:
- Broken URLs on the source website
- Network timeouts
- Files in unsupported formats
- Corrupted source files

The fetcher script logs these failures and continues processing.

## Future Enhancements

- [ ] Add support for Kenney.nl asset packs
- [ ] Add support for itch.io public domain assets
- [ ] Implement sprite sheet analysis (frame detection, dimensions)
- [ ] Add image preprocessing pipeline
- [ ] Create augmented versions of sprites
- [ ] Build sprite sheet metadata analyzer
- [ ] Add visualization tools for the corpus
- [ ] Create a web interface for browsing sprites

## Contributing

To add more sprite sheets to the corpus:

1. Ensure they are public domain or CC0-licensed
2. Add the source to `fetch_sprites.py`
3. Follow the existing metadata schema
4. Run the fetcher and splitter scripts
5. Update this documentation

## Resources

- [OpenGameArt.org](https://opengameart.org) - Original sprite sheet source
- [Hugging Face Dataset](https://huggingface.co/datasets/nyuuzyou/OpenGameArt-CC0) - Structured dataset
- [Kenney.nl](https://kenney.nl/assets) - High-quality CC0 game assets
- [itch.io Game Assets](https://itch.io/game-assets/free) - Free community assets
- [CC0 License Info](https://creativecommons.org/publicdomain/zero/1.0/) - License details

## Contact

For questions or issues with the corpus, please open an issue on the GitHub repository.

---

**Last Updated:** 2025-11-12
**Maintainer:** Russell Ballestrini
**Repository:** https://github.com/russellballestrini/sprite-sheet
