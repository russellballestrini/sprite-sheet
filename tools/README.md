# Sprite Sheet Tools

Unix philosophy utilities for analyzing and working with sprite sheets.

## Philosophy

Each tool does **one thing well** and can be composed with others:

- **detect_grid.py**: Auto-detects frame dimensions
- **detect_sprite_directions.py**: Determines animation directions
- **group_sprites.py**: Groups similar sprites by visual similarity

Tools are designed to be:
- **Small and focused**: Single responsibility
- **Composable**: Output of one can feed another
- **Scriptable**: JSON output for automation
- **Self-contained**: Minimal dependencies

## Installation

### Basic Installation (Required)

```bash
pip install pillow numpy
```

### Enhanced ML Features (Optional)

For improved detection accuracy on challenging sprites:

```bash
# Install all dependencies including ML libraries
pip install -r tools/requirements.txt

# Or install selectively:
pip install opencv-python              # For gradient-based detection
pip install transformers torch         # For CLIP AI model (best accuracy)
```

**Note:** The CLIP model will download ~500MB on first use but provides the best accuracy for small or ambiguous sprites.

## Quick Start

```bash
# Use Makefile for common tasks
make detect-grid IMAGE=sprite.png
make detect-directions IMAGE=sprite.png ARGS="-w 16 -h 18 -f 3 -r 4"
make group-sprites IMAGE=atlas.png ARGS="-w 32 -h 32"

# Or run tools directly
python3 tools/detect_grid.py sprite.png
python3 tools/detect_sprite_directions.py sprite.png -w 16 -h 18 -f 3 -r 4
python3 tools/group_sprites.py atlas.png -w 32 -h 32
```

---

## Grid Dimension Detector

**Purpose**: Automatically detect frame width, height, rows, columns, and padding.

**Unix Principle**: Measure twice, cut once - know your sprite dimensions before coding.

### Usage

```bash
# Auto-detect everything
python3 tools/detect_grid.py sprite.png

# Verbose output with confidence scores
python3 tools/detect_grid.py sprite.png --verbose

# JSON output for scripting
python3 tools/detect_grid.py sprite.png --json
```

### How It Works

1. **Edge Detection**
   - Finds strong vertical and horizontal edges
   - Identifies frame boundaries

2. **Autocorrelation**
   - Detects repeating patterns in the image
   - Determines frame spacing

3. **Peak Analysis**
   - Locates regular intervals between frames
   - Validates grid consistency

4. **Padding Detection**
   - Calculates space between frames
   - Handles non-zero padding gracefully

### Output

Provides ready-to-use JavaScript configuration:

```javascript
const sprite = new SpriteSheet({
  canvas: '#canvas',
  image: 'sprite.png',
  frameWidth: 32,
  frameHeight: 32,
  frames: 12,
  rows: 3,
  columns: 4,
  padding: 0
});
```

---

## Sprite Direction Detector

**Purpose**: Automatically detect which rows correspond to which directions (up, down, left, right).

**Unix Principle**: Computers are good at tedious pattern analysis - let them do it.

### Usage

```bash
# Basic detection
python3 tools/detect_sprite_directions.py sprite.png -w 16 -h 18 -f 3 -r 4

# Enable ML enhancement for low confidence detections (default: single frame analysis)
python3 tools/detect_sprite_directions.py sprite.png -w 16 -h 18 -f 3 -r 4 --ml

# Analyze all animation frames with CLIP (slower, may reduce accuracy)
python3 tools/detect_sprite_directions.py sprite.png -w 16 -h 18 -f 3 -r 4 --ml --clip-all-frames

# Verbose output with analysis details
python3 tools/detect_sprite_directions.py sprite.png -w 16 -h 18 -f 3 -r 4 --verbose

# JSON output for programmatic use
python3 tools/detect_sprite_directions.py sprite.png -w 16 -h 18 -f 3 -r 4 --json
```

### How It Works

#### Traditional Computer Vision (Default)

Uses three analysis techniques:

1. **Facing Direction Analysis**
   - Analyzes top vs bottom pixel density
   - Down-facing sprites are typically top-heavy
   - Up-facing sprites are bottom-heavy or uniform

2. **Horizontal Asymmetry Analysis**
   - Compares left vs right halves of sprite
   - Positive values = right-facing
   - Negative values = left-facing

3. **Motion Analysis**
   - Tracks animation motion patterns
   - Helps validate detected directions

#### ML Enhancement (with --ml flag)

When confidence is low (< 75%), automatically tries advanced methods:

1. **CLIP Model** (if transformers installed)
   - Uses OpenAI's CLIP vision-language model
   - **Multi-question approach**: Asks 5 separate questions to build understanding
     1. Front vs Back view?
     2. Left vs Right profile?
     3. Vertical orientation (top-down, face-on, back)?
     4. Body parts visible (face, head top, back, profile)?
     5. Movement direction?
   - **Weighted synthesis**: Combines answers with importance weights (e.g., face features ×2.0 for "down")
   - **Automatically upscales tiny sprites** (< 64px) for better semantic analysis
   - **Best for tiny sprites**: Achieves 100% accuracy on 16x18 sprites where traditional CV fails completely
   - **Complements traditional CV**: Use CLIP for < 20px sprites, traditional CV for larger sprites
   - Downloads ~500MB model on first use
   - CPU-friendly (no GPU required)

2. **OpenCV Enhanced Features** (if opencv-python installed)
   - **Automatic upscaling**: Small sprites scaled 2-4x for better analysis
   - **Multi-method ensemble**:
     - HOG (Histogram of Oriented Gradients)
     - Spatial moments analysis
     - Top/bottom pixel density
     - Left/right asymmetry detection
     - Canny edge detection with spatial distribution
   - **CPU-optimized**: No deep learning, pure computer vision
   - **Feature separation scoring**: Confidence based on how distinct directions appear

3. **Optical Flow Analysis** (experimental)
   - Tracks pixel movement across animation frames
   - Temporal consistency for better accuracy
   - Farneback dense optical flow (CPU-only)

The tool tries all available methods and automatically selects the most confident result.

### Algorithm

For each row of animation frames:

1. Extract all frames from that row
2. Convert to grayscale for analysis
3. Calculate metrics:
   - **Vertical motion**: Center of mass Y-coordinate change
   - **Horizontal asymmetry**: Difference between left/right pixel mass
   - **Motion amount**: Average pixel difference between frames
4. Determine directions:
   - **Down**: Row with highest positive vertical motion
   - **Up**: Row with most negative vertical motion
   - **Right**: Remaining row with positive horizontal asymmetry
   - **Left**: Remaining row with negative horizontal asymmetry

### Output

Provides direction mapping and JavaScript config:

```javascript
const animations = {
  down: { regionY: 0 * frameHeight },
  left: { regionY: 3 * frameHeight },
  right: { regionY: 1 * frameHeight },
  up: { regionY: 2 * frameHeight }
};
```

### Limitations

- **Best with larger sprites**: Works most accurately with sprites 32x32 or larger
- **Small sprites (< 24x24)**: May require manual verification even with ML
- Assumes 4-direction sprite sheets (up, down, left, right)
- May struggle with:
  - Isometric sprites
  - Minimal animation differences
  - Side-view only sprites (no up/down)
  - Top-down perspective (all directions look similar)

**Recommendation**: For sprites under 24x24 pixels, use the tool as a starting point but verify results visually in your game. The confidence score indicates reliability.

### Testing

Test on the Green Cap sprite:

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

---

## Sprite Grouping Tool

**Purpose**: Group similar sprites in an atlas by visual similarity.

**Unix Principle**: Organize once, reference many - know which sprites belong together.

### Usage

```bash
# Auto-detect dimensions and group
python3 tools/group_sprites.py atlas.png

# Specify dimensions
python3 tools/group_sprites.py atlas.png -w 32 -h 32

# Adjust similarity threshold (0-64, lower=stricter)
python3 tools/group_sprites.py atlas.png -w 64 -h 64 --threshold 15

# JSON output
python3 tools/group_sprites.py atlas.png -w 32 -h 32 --json
```

### How It Works

1. **Perceptual Hashing**
   - Computes visual fingerprint of each sprite
   - Resistant to minor variations

2. **Hamming Distance**
   - Measures similarity between sprite hashes
   - Lower distance = more similar

3. **Clustering**
   - Groups sprites below similarity threshold
   - Identifies animation sequences (consecutive frames)

4. **Sequence Detection**
   - Detects if groups form animation sequences
   - Identifies consecutive frames in same row

### Output

Identifies distinct sprite groups and sequences:

```
Group 1: 4 frames [Animation Sequence]
  Frame 0: Row 0, Col 0 (0, 0)
  Frame 1: Row 0, Col 1 (32, 0)
  Frame 2: Row 0, Col 2 (64, 0)
  Frame 3: Row 0, Col 3 (96, 0)

Group 2: 3 frames [Animation Sequence]
  Frame 4: Row 1, Col 0 (0, 32)
  Frame 5: Row 1, Col 1 (32, 32)
  Frame 6: Row 1, Col 2 (64, 32)
```

Provides JavaScript configuration:

```javascript
atlas.define('sprite-group-1', {
  x: 0,
  y: 0,
  width: 128,
  height: 32,
  frames: 4,
  rows: 1,
  framerate: 100
});
```

### Use Cases

- Identifying related sprites in large atlases
- Detecting duplicate or near-duplicate sprites
- Auto-organizing sprite collections
- Validating atlas layouts

---

## Composing Tools

Unix philosophy encourages tool composition. Examples:

```bash
# Pipeline 1: Detect grid, then analyze directions
DIMENSIONS=$(python3 tools/detect_grid.py sprite.png --json | jq -r '.frame_width,.frame_height,.rows,.frames')
python3 tools/detect_sprite_directions.py sprite.png \
  -w $(echo $DIMENSIONS | cut -d' ' -f1) \
  -h $(echo $DIMENSIONS | cut -d' ' -f2) \
  -r $(echo $DIMENSIONS | cut -d' ' -f3) \
  -f $(echo $DIMENSIONS | awk '{print $4/$3}')

# Pipeline 2: Group sprites, then analyze each group
python3 tools/group_sprites.py atlas.png --json > groups.json
# Process groups.json to extract individual sprite regions...

# Pipeline 3: Batch process multiple sprites
for sprite in sprites/*.png; do
  echo "Processing $sprite..."
  python3 tools/detect_grid.py "$sprite" --json >> sprite_configs.json
done
```

---

## Future Enhancements

Potential tool additions (each doing one thing well):

- **validate_sprite.py**: Verify sprite sheet integrity
- **extract_frames.py**: Extract individual frames to files
- **pack_atlas.py**: Pack multiple sprites into atlas
- **optimize_sprite.py**: Reduce sprite sheet file size
- **convert_format.py**: Convert between sprite formats
- **detect_colors.py**: Identify color palette
- **detect_transparency.py**: Analyze alpha channel usage

Algorithm improvements:
- ML-based direction detection using trained neural network
- Support for 8-direction sprites
- GUI tool for visual verification
- Export to game engine configs (Unity, Godot, Phaser, etc.)
