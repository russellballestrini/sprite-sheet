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

    // Create a sprite sheet
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
