# Multi-License Sprite Sheet Corpus Guide

## Overview

This project now supports downloading sprite sheets and 3D models from multiple licenses, organized for training and reference purposes.

## Directory Structure

```
corpus/
├── cc0/              # CC0 (Public Domain) - TRAINABLE
│   ├── raw/          # Sprite sheet images
│   └── metadata/     # JSON metadata files
│
├── cc-by/            # CC-BY-3.0 (Attribution) - TRAINABLE
│   ├── raw/
│   └── metadata/
│
├── cc-by-sa/         # CC-BY-SA-3.0 (Attribution + ShareAlike) - TRAINABLE
│   ├── raw/
│   └── metadata/
│
├── gpl/              # GPL-3.0 - NOT TRAINABLE (reference only)
│   ├── raw/
│   └── metadata/
│
└── 3d/               # 3D models for 360° screenshot generation
    ├── cc0/
    │   ├── raw/      # .blend, .obj, .fbx files
    │   └── metadata/
    ├── cc-by/
    ├── cc-by-sa/
    └── gpl/
```

## License Types

### CC0 (Public Domain)
- **Use**: Completely free, no attribution required
- **Trainable**: ✅ Yes
- **Commercial**: ✅ Yes
- **Modification**: ✅ Yes
- **Best for**: Training AI models, commercial games

### CC-BY-3.0 (Attribution)
- **Use**: Free with attribution to the creator
- **Trainable**: ✅ Yes
- **Commercial**: ✅ Yes (with attribution)
- **Modification**: ✅ Yes (with attribution)
- **Best for**: Training AI models, projects where attribution is acceptable

### CC-BY-SA-3.0 (Attribution + ShareAlike)
- **Use**: Free with attribution, derivative works must use same license
- **Trainable**: ✅ Yes
- **Commercial**: ✅ Yes (with attribution, derivatives stay CC-BY-SA)
- **Modification**: ✅ Yes (must share under CC-BY-SA)
- **Best for**: Training AI models, open-source projects

### GPL-3.0 (GNU General Public License)
- **Use**: Free for GPL-compatible projects only
- **Trainable**: ❌ No (kept for reference only)
- **Commercial**: ⚠️  Only in GPL projects
- **Modification**: ✅ Yes (must release as GPL)
- **Best for**: Reference, study, GPL open-source games

## Make Commands

### Fetch Trainable Licenses Only (Recommended)
```bash
# Download CC0, CC-BY, and CC-BY-SA 2D assets
make fetch-multi
```

### Fetch Everything
```bash
# Download all licenses (CC0, CC-BY, CC-BY-SA, GPL) and all types (2D + 3D)
make fetch-multi-all
```

### Fetch 3D Models for Screenshot Generation
```bash
# Download 3D models from all licenses for 360° view rendering
make fetch-3d
```

### Fetch GPL Assets (Reference Only)
```bash
# Download GPL assets (NOT for training, reference only)
make fetch-gpl
```

### Custom Fetch
```bash
# Fetch specific licenses and splits
python3 fetch_multi_license.py --licenses cc0 cc-by --splits 2d_art

# With target count per license/split
python3 fetch_multi_license.py --licenses all --splits all --target-per-license 1000
```

## Metadata Format

Each asset has a JSON metadata file containing:

```json
{
  "id": "unique_hash_id",
  "source": "nyuuzyou/OpenGameArt-CC0",
  "url": "https://opengameart.org/content/...",
  "title": "Asset Title",
  "author": "Artist Name",
  "author_url": "https://opengameart.org/users/...",
  "post_date": "2023-01-15",
  "license": "CC0-1.0",
  "trainable": true,
  "tags": ["sprite", "character", "animation"],
  "description": "Asset description...",
  "file_url": "https://...",
  "file_name": "sprite.png",
  "local_path": "corpus/cc0/raw/abc123.png",
  "asset_type": "2d"
}
```

## Training Workflow

### 1. Download Trainable Assets
```bash
# Get all trainable 2D assets (CC0, CC-BY, CC-BY-SA)
make fetch-multi
```

### 2. Prepare Training Data
```bash
# Analyze and detect sprite sheet layouts
make analyze-chars
make detect-layout

# Run ETL pipeline to extract individual frames
make etl-pipeline
```

### 3. Filter by License for Training
```python
import json
from pathlib import Path

# Load only CC0 assets (no attribution needed)
cc0_dir = Path("corpus/cc0/metadata")
assets = []
for meta_file in cc0_dir.glob("*.json"):
    with open(meta_file) as f:
        asset = json.load(f)
        if asset['trainable']:
            assets.append(asset)
```

## 3D Model → 360° Screenshot Workflow

### 1. Download 3D Models
```bash
make fetch-3d
```

### 2. Generate 360° Views (Future Feature)
Using AssetImporter (Assimp) to:
1. Load 3D model (.blend, .obj, .fbx)
2. Rotate camera 360° around the model
3. Take screenshots at intervals (e.g., every 10°)
4. Create a sprite sheet from the screenshots

This will be implemented as a separate tool.

## Dataset Sources

All assets are from OpenGameArt.org via Hugging Face datasets:

- **CC0**: `nyuuzyou/OpenGameArt-CC0`
  - ~7,300 2D assets
  - ~740 3D assets

- **CC-BY-3.0**: `nyuuzyou/OpenGameArt-CC-BY-3.0`
  - ~2,910 2D assets
  - ~313 3D assets

- **CC-BY-SA-3.0**: `nyuuzyou/OpenGameArt-CC-BY-SA-3.0`
  - ~967 2D assets
  - ~313 3D assets

- **GPL-3.0**: `nyuuzyou/OpenGameArt-GPL-3.0`
  - Various assets (reference only)

## Legal Notes

1. **Always attribute**: For CC-BY and CC-BY-SA assets, keep the author information in metadata
2. **GPL isolation**: GPL assets are kept separate and marked as non-trainable
3. **Training is derivative work**: When training AI models, we treat it as creating derivative works
4. **Commercial use**: CC0 and CC-BY assets are safe for commercial training; GPL is NOT

## Example: Training with Attribution

If using CC-BY or CC-BY-SA assets in your trained model, document the training data:

```
This model was trained on sprite sheets from OpenGameArt.org including:
- CC0 assets (public domain)
- CC-BY-3.0 assets by [list of authors]
- CC-BY-SA-3.0 assets by [list of authors]

Full attribution details: corpus/*/metadata/*.json
```

## Questions?

- For license questions: Check the `license` field in metadata JSON files
- For training suitability: Check the `trainable` boolean field
- For attribution requirements: Check `author` and `author_url` fields
