# Sprite Sheet Layout Detection System

## Overview
Auto-detection system for analyzing animated character sprite sheets and determining their grid layouts.

## Files Created

### 1. `analyze_animated_characters.py`
Filters the sprite corpus to identify animated character/enemy/player/NPC/animal sheets.

**Output:** `corpus/animated_character_sheets.json`

**Categories:**
- Characters (general sprites)
- Enemies (monsters, bosses)
- Players (heroes, protagonists)
- NPCs (non-player characters)
- Animals (creatures, beasts)

### 2. `detect_sprite_layout.py`
Automatically detects sprite sheet layouts using three methods:

**Methods:**
1. **Text Extraction** - Parses dimensions from title/description (e.g., "16x16")
2. **Computer Vision** - Detects sprite boundaries using transparency/empty regions
3. **Heuristic Guess** - Tests common sprite sizes (8x8, 16x16, 32x32, etc.)

**Output:** `corpus/sprite_layouts.json`

**Confidence Levels:**
- **High** - Perfect grid fit with text-extracted dimensions
- **Medium** - Good fit but some wasted space
- **Low** - Heuristic guess or poor fit
- **Unknown** - Could not detect layout

## Makefile Targets

```bash
# Analyze animated character sheets
make analyze-chars

# Detect sprite sheet layouts
make detect-layout

# Run full analysis pipeline
make analyze-full
```

## Results (Current Corpus)

From 149 animated character sprite sheets analyzed:

**Confidence Distribution:**
- High: 47 sheets (perfect grid detection)
- Medium: 29 sheets (good detection with minor issues)
- Low: 25 sheets (heuristic guesses)
- Unknown: 48 sheets (detection failed)

**Example High-Confidence Detections:**
- 16x16 8-bit RPG character set: 256x128px → 16x8 grid (128 frames)
- 16-bit skeleton: 544x32px → 34x1 strip (34 frames)
- 16x16 Animated Critters: 256x112px → 16x7 grid (112 frames)

## Data Structure

### sprite_layouts.json structure:
```json
{
  "id": "abc123",
  "title": "16x16 Character Sheet",
  "file": "corpus/raw/abc123.png",
  "image_width": 256,
  "image_height": 128,
  "confidence": "high",
  "best_layout": {
    "sprite_w": 16,
    "sprite_h": 16,
    "cols": 16,
    "rows": 8,
    "total_frames": 128,
    "perfect_fit": true,
    "waste_percentage": 0.0,
    "method": "text_extraction"
  }
}
```

## Next Steps

1. **Manual Review** - Review low/unknown confidence sheets
2. **Improve CV Detection** - Enhance computer vision algorithms
3. **Training Data Prep** - Use layout data to extract individual sprites
4. **Animation Detection** - Group frames into animation sequences
