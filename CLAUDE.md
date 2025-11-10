# Claude Code Guidelines for Sprite Sheet Library

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
│   └── SpriteSheet.js       # Core library
├── examples/
│   ├── simple-game.html     # Game example with arrow key controls
│   └── sprite-atlas.html    # Multi-sprite atlas example
├── demo.html                # Main interactive demo
├── index.html               # Entry point (same as demo.html)
├── index-legacy.html        # Legacy version
├── server.py                # Development server with proper MIME types
└── CLAUDE.md                # This file
```

## Development Server

Always use the custom Python server to serve files locally:

```bash
npm run serve
# or
python3 server.py
```

**Why?** The custom server sets proper MIME types for JavaScript modules, preventing CORS errors that occur with `file://` protocol or basic HTTP servers.

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

## Contributing

When making changes:
1. Use CSS Grid exclusively for layouts
2. Test with `npm run serve`
3. Ensure responsive behavior
4. Update this file if adding new patterns or guidelines
