# Sprite Sheet Library

A modern, lightweight HTML5 sprite sheet animation library for games and interactive web applications. Built with vanilla JavaScript ES6+ modules, zero dependencies, and a simple API perfect for code generation.

## Features

- 🚀 Modern ES6+ modules
- 📦 Zero dependencies
- 🎮 Perfect for game development
- 🔄 Support for multi-row sprite sheets
- ⚡ Efficient canvas rendering with requestAnimationFrame
- 🎯 Simple, chainable API
- 📱 Responsive and embeddable
- 🔧 Configurable frame padding and layout
- 💾 Support for both URLs and file uploads
- 🎨 Easy to use with AI code generation

## Demo

Check out the live demo: [View Demo](https://russellballestrini.github.io/sprite-sheet/)

### Running the Demo Locally

**Important:** To run the demos locally, you must use a web server due to CORS restrictions with ES6 modules. Simply opening the HTML files in your browser won't work.

```bash
# Start a local web server
npm run serve
```

Then open your browser to:
- http://localhost:8000/demo.html - Main demo
- http://localhost:8000/examples/simple-game.html - Simple game example
- http://localhost:8000/examples/sprite-atlas.html - Sprite atlas example

## Installation

### Via NPM (when published)

```bash
npm install @your-org/sprite-sheet
```

### Via CDN

```html
<script type="module">
  import { SpriteSheet } from 'https://cdn.jsdelivr.net/npm/@your-org/sprite-sheet/src/SpriteSheet.js';
</script>
```

### Direct Download

Download the `SpriteSheet.js` file and include it in your project:

```html
<script type="module">
  import { SpriteSheet } from './src/SpriteSheet.js';
</script>
```

## Quick Start

### Option 1: Specify Exact Dimensions

```html
<!DOCTYPE html>
<html>
<head>
  <title>My Sprite Animation</title>
</head>
<body>
  <canvas id="gameCanvas" width="640" height="480"></canvas>

  <script type="module">
    import { SpriteSheet } from './src/SpriteSheet.js';

    // Create a sprite sheet with exact dimensions
    const player = new SpriteSheet({
      canvas: '#gameCanvas',
      image: 'player-sprite.png',
      frameWidth: 32,
      frameHeight: 32,
      frames: 8,
      framerate: 100, // milliseconds per frame
      rows: 1,
      loop: true
    });

    // Wait for the image to load
    await player.ready();

    // Start the animation
    player.play();
  </script>
</body>
</html>
```

### Option 2: Auto-Detect Dimensions

```html
<script type="module">
  import { SpriteSheet } from './src/SpriteSheet.js';

  // Let the library calculate frame dimensions automatically!
  // For a sprite sheet with 12 frames in a 4x3 grid
  const player = new SpriteSheet({
    canvas: '#gameCanvas',
    image: 'player-sprite.png',
    frames: 12,     // Total number of frames
    rows: 4,        // 4 rows
    columns: 3,     // 3 columns (optional - auto-calculated if omitted)
    framerate: 100
    // frameWidth and frameHeight are calculated automatically!
  });

  await player.ready();
  console.log(player.getInfo()); // See auto-detected dimensions
  player.play();
</script>
```

## API Reference

### Constructor Options

```javascript
new SpriteSheet({
  canvas: '#myCanvas',      // Canvas element or selector (required)
  image: 'sprite.png',      // Image URL or data URL (required)
  frameWidth: 32,           // Width of each frame (default: 100)
  frameHeight: 32,          // Height of each frame (default: 100)
  frames: 8,                // Total number of frames (default: 1)
  framerate: 100,           // Milliseconds between frames (default: 60)
  padding: 0,               // Padding between frames (default: 0)
  rows: 1,                  // Number of rows in sprite sheet (default: 1)
  columns: 0,               // Number of columns (auto-calculated if 0)
  loop: true,               // Whether to loop animation (default: true)
  onFrameChange: (frame) => {}, // Callback on frame change
  onComplete: () => {}      // Callback when animation completes
});
```

### Methods

#### Animation Control

```javascript
// Play the animation
sprite.play();

// Pause/stop the animation
sprite.pause();
sprite.stop();

// Toggle play/pause
sprite.toggle();

// Reset to first frame
sprite.reset();
```

#### Frame Navigation

```javascript
// Go to a specific frame (0-based)
sprite.gotoFrame(5);

// Move to next frame
sprite.nextFrame();

// Move to previous frame
sprite.prevFrame();

// Draw a specific frame at position
sprite.drawFrame(frameIndex, x, y, width, height);
```

#### Configuration

```javascript
// Set framerate (milliseconds between frames)
sprite.setFramerate(100);

// Set framerate (frames per second)
sprite.setFramerate(10, true);

// Load a new image
await sprite.loadImage('new-sprite.png');

// Wait for image to load
await sprite.ready();
```

#### Cleanup

```javascript
// Clear the canvas
sprite.clear();

// Destroy and clean up resources
sprite.destroy();
```

## Advanced Examples

### Auto-Detecting Dimensions

The library can automatically calculate frame dimensions from your sprite sheet:

```javascript
// Example 1: Specify rows and columns
const sprite = new SpriteSheet({
  canvas: '#canvas',
  image: 'sprite-sheet.png',  // 256x128 image
  frames: 8,
  rows: 2,      // 2 rows
  columns: 4    // 4 columns
  // Automatically calculates: frameWidth=64, frameHeight=64
});

// Example 2: Let it calculate columns
const sprite2 = new SpriteSheet({
  canvas: '#canvas',
  image: 'sprite-sheet.png',
  frames: 12,
  rows: 3       // columns auto-calculated as 4
});

// Example 3: Get dimensions when loaded
const sprite3 = new SpriteSheet({
  canvas: '#canvas',
  image: 'sprite.png',
  frames: 6,
  rows: 2,
  onImageLoad: (info) => {
    console.log('Detected dimensions:', info);
    // { imageWidth, imageHeight, frameWidth, frameHeight, rows, columns }
  }
});
```

### Sprite Atlas (Multiple Sprites on One Sheet)

Perfect for games with many characters/monsters on a single texture atlas:

```javascript
import { SpriteAtlas } from './src/SpriteSheet.js';

// Create atlas from a single image containing all game sprites
const atlas = new SpriteAtlas('#canvas', 'game-atlas.png');
await atlas.ready();

// Define different character regions in the atlas
atlas
  .define('player-idle', {
    x: 0, y: 0,           // Position in atlas
    width: 192,           // Width of this sprite region
    height: 32,           // Height of this sprite region
    frames: 6,            // Number of frames
    rows: 1,
    framerate: 100
  })
  .define('player-walk', {
    x: 0, y: 32,          // Below idle animation
    width: 256,
    height: 32,
    frames: 8,
    rows: 1
  })
  .define('enemy-goblin', {
    x: 0, y: 64,
    width: 128,
    height: 32,
    frames: 4,
    rows: 1
  })
  .define('enemy-dragon', {
    x: 0, y: 96,
    width: 320,
    height: 64,
    frames: 10,
    rows: 1,
    framerate: 80
  });

// Play any sprite by name
await atlas.play('player-idle');

// Switch to a different sprite
await atlas.play('enemy-goblin');

// Get a specific sprite for manual control
const playerWalk = atlas.get('player-walk');
playerWalk.play();

// List all defined sprites
console.log(atlas.list()); // ['player-idle', 'player-walk', 'enemy-goblin', 'enemy-dragon']

// Stop all animations
atlas.stopAll();
```

### Sprite Regions (Part of a Larger Atlas)

Extract a specific region from a larger sprite sheet:

```javascript
// Use only a specific region of a large atlas
const sprite = new SpriteSheet({
  canvas: '#canvas',
  image: 'mega-atlas.png',    // Large 2048x2048 atlas
  regionX: 512,                // Start at x=512
  regionY: 256,                // Start at y=256
  regionWidth: 256,            // Use 256px wide
  regionHeight: 64,            // Use 64px tall
  frames: 8,
  rows: 1
  // Frames will be extracted from the specified region
});
```

### Multiple Animations

```javascript
import { SpriteSheet } from './src/SpriteSheet.js';

const animations = {
  idle: new SpriteSheet({
    canvas: '#player',
    image: 'player-idle.png',
    frameWidth: 32,
    frameHeight: 32,
    frames: 4,
    framerate: 200,
    rows: 1
  }),

  walk: new SpriteSheet({
    canvas: '#player',
    image: 'player-walk.png',
    frameWidth: 32,
    frameHeight: 32,
    frames: 8,
    framerate: 100,
    rows: 1
  }),

  jump: new SpriteSheet({
    canvas: '#player',
    image: 'player-jump.png',
    frameWidth: 32,
    frameHeight: 32,
    frames: 6,
    framerate: 80,
    rows: 1,
    loop: false
  })
};

// Wait for all to load
await Promise.all([
  animations.idle.ready(),
  animations.walk.ready(),
  animations.jump.ready()
]);

// Play an animation
let current = animations.idle;
current.play();

// Switch animations
function switchAnimation(name) {
  current.stop();
  current = animations[name];
  current.reset().play();
}
```

### Multi-Row Sprite Sheets

```javascript
// Sprite sheet with 4 rows and 3 columns
const character = new SpriteSheet({
  canvas: '#canvas',
  image: 'character-directions.png',
  frameWidth: 32,
  frameHeight: 32,
  frames: 12,  // 4 rows × 3 frames each
  rows: 4,
  columns: 3,
  framerate: 150
});

await character.ready();
character.play();
```

### File Upload

```javascript
import { fromFile } from './src/SpriteSheet.js';

document.getElementById('fileInput').addEventListener('change', async (e) => {
  const file = e.target.files[0];

  if (file) {
    const sprite = await fromFile(file, {
      canvas: '#canvas',
      frameWidth: 32,
      frameHeight: 32,
      frames: 8,
      framerate: 100
    });

    sprite.play();
  }
});
```

### Custom Rendering with drawFrame

```javascript
const sprite = new SpriteSheet({
  canvas: '#canvas',
  image: 'sprite.png',
  frameWidth: 64,
  frameHeight: 64,
  frames: 16,
  rows: 4
});

await sprite.ready();

// Manually control which frame to draw and where
function gameLoop() {
  sprite.clear();

  // Draw frame 0 at position (50, 50) with double size
  sprite.drawFrame(0, 50, 50, 128, 128);

  // Draw frame 5 at position (200, 100) with normal size
  sprite.drawFrame(5, 200, 100);

  requestAnimationFrame(gameLoop);
}

gameLoop();
```

### Frame Change Callbacks

```javascript
const sprite = new SpriteSheet({
  canvas: '#canvas',
  image: 'sprite.png',
  frameWidth: 32,
  frameHeight: 32,
  frames: 8,
  framerate: 100,
  onFrameChange: (frameIndex) => {
    console.log(`Now showing frame ${frameIndex}`);

    // Trigger sound effects on specific frames
    if (frameIndex === 3) {
      playSound('step.mp3');
    }
  },
  onComplete: () => {
    console.log('Animation completed!');
    // Do something when animation finishes (only if loop: false)
  }
});

await sprite.ready();
sprite.play();
```

## Use Cases

### Game Development

Perfect for 2D game sprites, character animations, UI elements, and particle effects.

### Interactive Web Apps

Add life to your web applications with animated icons, loading indicators, and interactive elements.

### AI Code Generation

The simple, declarative API makes it ideal for AI-powered code generation tools. The library handles all the complexity of sprite sheet rendering and animation.

### Educational Projects

Great for learning game development, HTML5 canvas, and animation principles.

## Browser Support

- Modern browsers with ES6+ module support
- Chrome/Edge 61+
- Firefox 60+
- Safari 11+
- Opera 48+

For older browsers, use the UMD build after running `npm run build`.

## Building

```bash
# Install dependencies
npm install

# Build all formats (ES, UMD, CommonJS)
npm run build

# Development mode with watch
npm run dev

# Start local server for demo
npm run serve
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this in your projects!

## Credits

Originally created by [is-a-cat](https://github.com/is-a-cat) for Project Phoenix.
Modernized and enhanced for embedding and game development.

## Resources

- [OpenGameArt.org](https://opengameart.org) - Free sprite sheets
- [itch.io](https://itch.io/game-assets/free) - Free game assets
- [Sprite Database](https://www.spriters-resource.com/) - Sprite resources

## Support

For issues, questions, or suggestions, please [open an issue](https://github.com/russellballestrini/sprite-sheet/issues) on GitHub.
