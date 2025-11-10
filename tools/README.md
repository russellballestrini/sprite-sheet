# Sprite Sheet Tools

Utilities for analyzing and working with sprite sheets.

## Sprite Direction Detector

Automatically detects which rows in a sprite sheet correspond to which directions (up, down, left, right).

### Installation

```bash
pip install pillow numpy
```

### Usage

```bash
python3 tools/detect_sprite_directions.py <image> -w <width> -h <height> -f <frames> -r <rows>
```

### Examples

**Basic detection:**
```bash
python3 tools/detect_sprite_directions.py sprite.png -w 16 -h 18 -f 3 -r 4
```

**Verbose output with analysis details:**
```bash
python3 tools/detect_sprite_directions.py sprite.png -w 16 -h 18 -f 3 -r 4 --verbose
```

**JSON output for programmatic use:**
```bash
python3 tools/detect_sprite_directions.py sprite.png -w 16 -h 18 -f 3 -r 4 --json
```

### How It Works

The detector uses multiple computer vision techniques:

1. **Vertical Motion Detection**
   - Tracks center of mass across animation frames
   - Detects upward vs downward movement
   - Identifies up/down facing animations

2. **Horizontal Asymmetry Analysis**
   - Compares left vs right halves of sprite
   - Detects which direction the character is facing
   - Distinguishes left-facing from right-facing animations

3. **Motion Amount**
   - Measures overall pixel changes between frames
   - Helps identify which rows are more animated
   - Useful for validation

### Output

The script provides:
- Direction mapping (which row = which direction)
- JavaScript configuration snippet
- Detailed analysis (with `--verbose`)
- JSON output (with `--json`)

### Algorithm Details

For each row of animation frames, the detector:

1. Extracts all frames from that row
2. Converts to grayscale for analysis
3. Calculates:
   - **Vertical motion**: Center of mass Y-coordinate change
   - **Horizontal asymmetry**: Difference between left/right pixel mass
   - **Motion amount**: Average pixel difference between frames

4. Determines directions by:
   - **Down**: Row with highest positive vertical motion
   - **Up**: Row with most negative vertical motion
   - **Right**: Remaining row with positive horizontal asymmetry
   - **Left**: Remaining row with negative horizontal asymmetry

### Limitations

- Works best with clear directional animations
- Assumes 4-direction sprite sheets (up, down, left, right)
- May struggle with:
  - Isometric sprites
  - Minimal animation differences
  - Side-view only sprites (no up/down)

### Testing

Test on the included Green Cap sprite:

```bash
# Download test sprite
curl -O https://opengameart.org/sites/default/files/Green-Cap-Character-16x18.png

# Run detection
python3 tools/detect_sprite_directions.py Green-Cap-Character-16x18.png \
  -w 16 -h 18 -f 3 -r 4 --verbose
```

Expected output:
```
  down: Row 0
  left: Row 3
  right: Row 1
  up: Row 2
```

## Future Enhancements

Potential improvements:
- ML-based detection using trained neural network
- Support for 8-direction sprites
- Automatic frame dimension detection
- GUI tool for visual verification
- Batch processing for multiple sprites
- Export to game engine configs (Unity, Godot, etc.)
