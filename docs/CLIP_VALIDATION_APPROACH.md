# CLIP-Based Sprite Sheet Validation

## Problem
We need to determine sprite dimensions with 100% certainty. Traditional detection methods can guess dimensions but can't verify if the subject is properly framed.

## Solution: CLIP Validation
Use OpenAI's CLIP model to validate that detected sprite dimensions are correct by checking if the subject (character/enemy/NPC/animal) is properly centered in the extracted frame.

## How It Works

### 1. Layout Detection (existing)
- Extract dimensions from title/description
- Use computer vision to detect boundaries
- Heuristic guessing for common sizes

### 2. CLIP Validation (new)
For each detected layout:
1. **Sample 4 frames** from different positions (start, quarter, middle, end)
2. **Extract each frame** using detected dimensions
3. **Use CLIP** to score each frame against prompts:
   - ✅ "a character sprite centered in frame"
   - ✅ "a complete character in the center"
   - ❌ "an empty frame"
   - ❌ "a cropped character at the edge"
   - ❌ "partial sprite cut off"
4. **Calculate confidence**: (centered_score - bad_score)
5. **Validate**: confidence > threshold = dimensions are correct

### 3. Results
- **Validated**: Dimensions are 100% correct, subject is centered
- **Failed**: Dimensions are wrong, needs manual review or re-detection
- **Pass to Claude**: Failed cases for human review

## Benefits

1. **No wasted extraction**: Only sample 4 frames, not all frames
2. **Semantic validation**: CLIP understands if a character is properly framed
3. **High accuracy**: Visual AI validation beats pure math/heuristics
4. **Clear outputs**: Binary validated/failed decision
5. **Scalable**: Can process thousands of sheets efficiently

## Pipeline Flow

```
Sprite Sheets
    ↓
Detect Layout (detect_sprite_layout.py)
    ↓
Validate with CLIP (validate_layout_with_clip.py)
    ├─→ Validated (100% confident) → Ready for training
    └─→ Failed → needs_review/ → Pass to Claude
```

## Usage

```bash
# Full pipeline
make analyze-chars    # Filter animated characters
make detect-layout    # Detect grid dimensions  
make validate-clip    # Validate with CLIP

# Or all at once
make analyze-full && make validate-clip
```

## Output Files

- `corpus/validated_layouts.json` - CLIP validation results
- `corpus/needs_review/` - Sprite sheets that need manual review
- Only validated sheets proceed to training data preparation

## Requirements

- PyTorch
- OpenAI CLIP
- See requirements.txt

