# Claude Code Guidelines for Sprite Sheet Library

## Project Overview

Modern HTML5 sprite sheet animation library with **zero dependencies**, ES6+ modules, and Unix philosophy command-line tools for sprite analysis.

### Core Philosophy
- **Zero dependencies** for the JavaScript library
- **Unix philosophy** for CLI tools: small, focused, composable
- **Python virtual environment** for tool isolation
- **Makefile-driven** workflow (no npm for tools)
- **Data-driven** improvement via ground truth corpus

## CSS Layout Standards

### Use CSS Grid Exclusively

All layouts in this project should use **CSS Grid** for consistency and modern best practices. Avoid using Flexbox for layout purposes.

#### Common Grid Patterns

**1. Centering Content**
```css
.container {
  display: grid;
  place-items: center;
}
```

**2. Column Layouts**
```css
/* Two equal columns */
.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

/* Three equal columns */
.grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
}

/* Responsive columns with minimum width */
.button-group {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 10px;
}
```

**3. Vertical Stacking**
```css
.control-group {
  display: grid;
  gap: 8px;
}
```

**4. Page Layout**
```css
body {
  display: grid;
  place-items: center;
  min-height: 100vh;
  gap: 20px;
}
```

### Why Grid Over Flex?

- **Consistency**: Using a single layout system across the codebase
- **Simplicity**: Grid handles both 1D and 2D layouts
- **Maintainability**: Easier to understand and modify
- **Modern**: Grid is the current standard for web layouts

### Grid Properties Reference

| Property | Common Values | Use Case |
|----------|--------------|----------|
| `display: grid` | - | Enable grid layout |
| `grid-template-columns` | `1fr 1fr`, `repeat(3, 1fr)`, `repeat(auto-fit, minmax(100px, 1fr))` | Define column structure |
| `gap` | `10px`, `15px`, `20px` | Spacing between grid items |
| `place-items` | `center`, `start`, `end` | Align and justify items |
| `grid-column` | `2`, `1 / 3`, `span 2` | Item column placement |

## File Structure

```
sprite-sheet/
├── src/
│   └── SpriteSheet.js              # Core library (zero dependencies)
├── examples/
│   ├── simple-game.html            # Game example (arrow keys + WASD)
│   └── sprite-atlas.html           # Multi-sprite atlas example
├── tools/                          # Unix philosophy CLI tools
│   ├── venv/                       # Python virtual environment (gitignored)
│   ├── detect_grid.py              # Auto-detect frame dimensions
│   ├── detect_sprite_directions.py # Detect sprite facing directions
│   ├── group_sprites.py            # Group similar sprites by visual similarity
│   ├── benchmark.py                # Accuracy benchmark against corpus
│   ├── corpus.json                 # Ground truth dataset for testing
│   ├── requirements.txt            # Python dependencies
│   └── README.md                   # Tool documentation
├── demo.html                       # Main interactive demo
├── index.html                      # Entry point (same as demo.html)
├── server.py                       # Development server with proper MIME types
├── Makefile                        # Unix-style build system
└── CLAUDE.md                       # This file
```

## Development Workflow

### Running the Development Server

```bash
make serve
# or directly:
python3 server.py
```

**Why?** The custom server sets proper MIME types for JavaScript modules, preventing CORS errors that occur with `file://` protocol or basic HTTP servers.

### Setting Up Python Tools

**First time setup:**
```bash
make install-tools    # Creates venv, installs pillow + numpy
make install-ml       # Optional: installs OpenCV, PyTorch CPU, Transformers
```

**Tools are isolated in `tools/venv/`** - never install to system Python!

### Using the Tools

All tools are invoked via Makefile for consistency:

```bash
# Auto-detect sprite grid dimensions
make detect-grid IMAGE=sprite.png

# Detect animation directions (up, down, left, right)
make detect-directions IMAGE=sprite.png ARGS='-w 16 -H 18 -f 3 -r 4'
make detect-directions IMAGE=sprite.png ARGS='-w 16 -H 18 -f 3 -r 4 --ml'

# Group similar sprites in atlas
make group-sprites IMAGE=atlas.png ARGS='-w 32 -h 32'

# Run accuracy benchmark
make benchmark

# Test all tools
make test-tools

# Clean up
make clean       # Remove temp files
make clean-all   # Remove temp files + venv
```

## Code Style

### JavaScript
- Use ES6+ module syntax
- Use `async/await` for asynchronous operations
- Class-based architecture
- Descriptive variable names

### HTML/CSS
- Use semantic HTML5 elements
- CSS Grid for all layouts
- Mobile-first responsive design
- Consistent spacing (multiples of 5px: 10px, 15px, 20px, etc.)

## Common Tasks

### Adding a New Demo Page

1. Create HTML file in `examples/` directory
2. Use CSS Grid for layout (see patterns above)
3. Import SpriteSheet: `import { SpriteSheet } from '../src/SpriteSheet.js';`
4. Add responsive meta tag: `<meta name="viewport" content="width=device-width, initial-scale=1.0">`
5. Test with `npm run serve`

### Modifying Layout

1. Identify the container element
2. Apply `display: grid`
3. Use appropriate grid properties (see reference above)
4. **Never** use `display: flex` or `display: inline-flex`

### Testing Sprite Rendering

For small sprites (< 32px), the demo automatically scales them 2-8x for visibility. This is handled in `demo.html` and `index.html` via the `DemoApp` class.

## Browser Support

The library uses modern JavaScript and CSS:
- ES6+ modules
- CSS Grid
- `async/await`
- `requestAnimationFrame`

Target browsers: Chrome/Edge 61+, Firefox 60+, Safari 11+, Opera 48+

## Core Algorithms

### Grid Detection (`detect_grid.py`)
- Edge detection (vertical/horizontal lines)
- Autocorrelation for repeating patterns
- Peak analysis for frame boundaries
- Padding detection

### Direction Detection (`detect_sprite_directions.py`)

**Traditional Computer Vision**
- Facing direction analysis (top vs bottom pixel density)
- Horizontal asymmetry detection (left vs right mass)
- Motion analysis (center of mass tracking)

**OpenCV Enhanced**
- Multi-feature ensemble (HOG, spatial moments, edge detection)
- Automatic upscaling for small sprites (2-4x)
- Feature separation confidence scoring

**CLIP Vision Model** (Key Breakthrough)
- **Analyzes single frames** to determine "which way is this character facing?"
- Compares each frame against semantic descriptions:
  - "a game character viewed from above showing the top and front" (down)
  - "a game character viewed from above showing the back" (up)
  - "a game character shown from the side facing left/right"
- **Automatically upscales tiny sprites** (< 64px) for better semantic understanding
- **Averages scores across all animation frames** per row for robustness
- Works on **visual facing direction**, not animation motion patterns
- Currently achieves 50% accuracy on 16x18 Green Cap sprite (left/right correct)

### Sprite Grouping (`group_sprites.py`)
- Perceptual hashing for visual fingerprints
- Hamming distance for similarity measurement
- Clustering to identify animation sequences

### Accuracy Benchmarking (`benchmark.py`)
- Per-direction accuracy scoring (not just overall)
- Tests all methods (traditional, OpenCV, CLIP)
- Downloads missing test sprites automatically
- Ground truth corpus in `tools/corpus.json`

## Contributing

When making changes:
1. Use CSS Grid exclusively for layouts
2. Test with `make serve` (not npm)
3. Use Makefile for all tool operations
4. Never install Python packages to system (use venv)
5. Ensure responsive behavior
6. Update this file if adding new patterns or guidelines
