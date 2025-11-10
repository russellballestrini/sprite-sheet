/**
 * SpriteSheet - A modern, embeddable sprite sheet animation library
 * @class
 */
export class SpriteSheet {
  /**
   * Create a new SpriteSheet instance
   * @param {Object} options - Configuration options
   * @param {HTMLCanvasElement|string} options.canvas - Canvas element or selector
   * @param {string} options.image - Image URL or data URL
   * @param {number} [options.frameWidth] - Width of each frame (auto-detected if not provided)
   * @param {number} [options.frameHeight] - Height of each frame (auto-detected if not provided)
   * @param {number} [options.frames=1] - Total number of frames
   * @param {number} [options.framerate=60] - Milliseconds between frames
   * @param {number} [options.padding=0] - Padding between frames
   * @param {number} [options.rows=1] - Number of rows in sprite sheet
   * @param {number} [options.columns=0] - Number of columns (auto-calculated if 0)
   * @param {boolean} [options.loop=true] - Whether to loop the animation
   * @param {number} [options.regionX=0] - X offset for sprite region in atlas
   * @param {number} [options.regionY=0] - Y offset for sprite region in atlas
   * @param {number} [options.regionWidth] - Width of sprite region (defaults to image width)
   * @param {number} [options.regionHeight] - Height of sprite region (defaults to image height)
   * @param {Function} [options.onFrameChange] - Callback when frame changes
   * @param {Function} [options.onComplete] - Callback when animation completes
   * @param {Function} [options.onImageLoad] - Callback when image loads with dimensions
   */
  constructor(options = {}) {
    // Canvas setup
    this.canvas = typeof options.canvas === 'string'
      ? document.querySelector(options.canvas)
      : options.canvas;

    if (!this.canvas) {
      throw new Error('Canvas element not found');
    }

    this.ctx = this.canvas.getContext('2d');

    // Store options for after image loads
    this.options = options;

    // Sprite sheet parameters (may be updated after image loads)
    this.frameWidth = options.frameWidth || null;
    this.frameHeight = options.frameHeight || null;
    this.totalFrames = options.frames || 1;
    this.framerate = options.framerate || 60;
    this.padding = options.padding || 0;
    this.rows = options.rows || 1;
    this.columns = options.columns || 0;
    this.loop = options.loop !== undefined ? options.loop : true;

    // Region/atlas support (for extracting part of a larger sprite sheet)
    this.regionX = options.regionX || 0;
    this.regionY = options.regionY || 0;
    this.regionWidth = options.regionWidth || null;
    this.regionHeight = options.regionHeight || null;

    // Callbacks
    this.onFrameChange = options.onFrameChange || null;
    this.onComplete = options.onComplete || null;
    this.onImageLoad = options.onImageLoad || null;

    // Animation state
    this.currentFrame = 0;
    this.isPlaying = false;
    this.animationId = null;
    this.lastFrameTime = 0;

    // Image dimensions (filled after load)
    this.imageWidth = 0;
    this.imageHeight = 0;

    // Image loading
    this.image = new Image();
    this.imageLoaded = false;
    this.loadPromise = this._loadImage(options.image);
  }

  /**
   * Load the sprite sheet image
   * @private
   * @param {string} imageUrl - URL or data URL of the image
   * @returns {Promise} Resolves when image is loaded
   */
  _loadImage(imageUrl) {
    return new Promise((resolve, reject) => {
      if (!imageUrl) {
        reject(new Error('No image URL provided'));
        return;
      }

      this.image.onload = () => {
        this.imageLoaded = true;

        // Store actual image dimensions
        this.imageWidth = this.image.width;
        this.imageHeight = this.image.height;

        // Auto-detect dimensions if not provided
        this._autoDetectDimensions();

        // Call onImageLoad callback with detected info
        if (this.onImageLoad) {
          this.onImageLoad({
            imageWidth: this.imageWidth,
            imageHeight: this.imageHeight,
            frameWidth: this.frameWidth,
            frameHeight: this.frameHeight,
            rows: this.rows,
            columns: this.columns,
            totalFrames: this.totalFrames
          });
        }

        resolve(this);
      };

      this.image.onerror = () => {
        reject(new Error(`Failed to load image: ${imageUrl}`));
      };

      this.image.src = imageUrl;
    });
  }

  /**
   * Auto-detect frame dimensions based on image size and options
   * @private
   */
  _autoDetectDimensions() {
    // Determine region dimensions (portion of image we're using)
    const regionWidth = this.regionWidth || this.imageWidth;
    const regionHeight = this.regionHeight || this.imageHeight;

    // If columns specified but not frameWidth, calculate it
    if (!this.frameWidth && this.columns > 0) {
      this.frameWidth = Math.floor((regionWidth - this.padding) / this.columns) - this.padding;
    }

    // If rows specified but not frameHeight, calculate it
    if (!this.frameHeight && this.rows > 0) {
      this.frameHeight = Math.floor((regionHeight - this.padding) / this.rows) - this.padding;
    }

    // If still no dimensions, try to auto-detect based on totalFrames
    if (!this.frameWidth || !this.frameHeight) {
      // Calculate columns if not specified
      if (!this.columns) {
        this.columns = Math.ceil(this.totalFrames / this.rows);
      }

      // Calculate frame dimensions from available space
      if (!this.frameWidth) {
        this.frameWidth = Math.floor((regionWidth - this.padding) / this.columns) - this.padding;
      }

      if (!this.frameHeight) {
        this.frameHeight = Math.floor((regionHeight - this.padding) / this.rows) - this.padding;
      }
    }

    // Calculate columns if still not set
    if (!this.columns) {
      this.columns = Math.ceil(this.totalFrames / this.rows);
    }

    // Ensure we have valid dimensions
    if (this.frameWidth <= 0 || this.frameHeight <= 0) {
      console.warn('Unable to determine valid frame dimensions. Using defaults.');
      this.frameWidth = this.frameWidth || 100;
      this.frameHeight = this.frameHeight || 100;
    }
  }

  /**
   * Wait for the image to load
   * @returns {Promise<SpriteSheet>} Resolves with this instance when ready
   */
  async ready() {
    await this.loadPromise;
    return this;
  }

  /**
   * Get the source coordinates for a specific frame
   * @private
   * @param {number} frameIndex - Frame number (0-based)
   * @returns {Object} Object with x, y coordinates
   */
  _getFrameCoords(frameIndex) {
    const row = Math.floor(frameIndex / this.columns);
    const col = frameIndex % this.columns;

    return {
      x: this.regionX + col * (this.frameWidth + this.padding) + this.padding,
      y: this.regionY + row * (this.frameHeight + this.padding) + this.padding
    };
  }

  /**
   * Get information about the sprite sheet
   * @returns {Object} Sprite sheet information
   */
  getInfo() {
    return {
      imageWidth: this.imageWidth,
      imageHeight: this.imageHeight,
      frameWidth: this.frameWidth,
      frameHeight: this.frameHeight,
      totalFrames: this.totalFrames,
      rows: this.rows,
      columns: this.columns,
      padding: this.padding,
      regionX: this.regionX,
      regionY: this.regionY,
      regionWidth: this.regionWidth || this.imageWidth,
      regionHeight: this.regionHeight || this.imageHeight,
      currentFrame: this.currentFrame,
      isPlaying: this.isPlaying
    };
  }

  /**
   * Draw a specific frame
   * @param {number} [frameIndex] - Frame to draw (defaults to current frame)
   * @param {number} [x=0] - X position on canvas
   * @param {number} [y=0] - Y position on canvas
   * @param {number} [width] - Width to draw (defaults to frameWidth)
   * @param {number} [height] - Height to draw (defaults to frameHeight)
   * @returns {SpriteSheet} This instance for chaining
   */
  drawFrame(frameIndex, x = 0, y = 0, width, height) {
    if (!this.imageLoaded) {
      console.warn('Image not loaded yet');
      return this;
    }

    const frame = frameIndex !== undefined ? frameIndex : this.currentFrame;
    const coords = this._getFrameCoords(frame);
    const drawWidth = width || this.frameWidth;
    const drawHeight = height || this.frameHeight;

    this.ctx.clearRect(x, y, drawWidth, drawHeight);
    this.ctx.drawImage(
      this.image,
      coords.x,
      coords.y,
      this.frameWidth,
      this.frameHeight,
      x,
      y,
      drawWidth,
      drawHeight
    );

    return this;
  }

  /**
   * Go to a specific frame
   * @param {number} frameIndex - Frame number (0-based)
   * @returns {SpriteSheet} This instance for chaining
   */
  gotoFrame(frameIndex) {
    this.currentFrame = Math.max(0, Math.min(frameIndex, this.totalFrames - 1));
    this.drawFrame();

    if (this.onFrameChange) {
      this.onFrameChange(this.currentFrame);
    }

    return this;
  }

  /**
   * Go to the next frame
   * @returns {SpriteSheet} This instance for chaining
   */
  nextFrame() {
    this.currentFrame++;

    if (this.currentFrame >= this.totalFrames) {
      if (this.loop) {
        this.currentFrame = 0;
      } else {
        this.currentFrame = this.totalFrames - 1;
        this.stop();
        if (this.onComplete) {
          this.onComplete();
        }
        return this;
      }
    }

    this.drawFrame();

    if (this.onFrameChange) {
      this.onFrameChange(this.currentFrame);
    }

    return this;
  }

  /**
   * Go to the previous frame
   * @returns {SpriteSheet} This instance for chaining
   */
  prevFrame() {
    this.currentFrame--;

    if (this.currentFrame < 0) {
      this.currentFrame = this.loop ? this.totalFrames - 1 : 0;
    }

    this.drawFrame();

    if (this.onFrameChange) {
      this.onFrameChange(this.currentFrame);
    }

    return this;
  }

  /**
   * Start playing the animation
   * @returns {SpriteSheet} This instance for chaining
   */
  play() {
    if (this.isPlaying) {
      return this;
    }

    this.isPlaying = true;
    this.lastFrameTime = performance.now();
    this._animate();

    return this;
  }

  /**
   * Internal animation loop
   * @private
   */
  _animate() {
    if (!this.isPlaying) {
      return;
    }

    this.animationId = requestAnimationFrame(() => this._animate());

    const currentTime = performance.now();
    const deltaTime = currentTime - this.lastFrameTime;

    if (deltaTime >= this.framerate) {
      this.lastFrameTime = currentTime - (deltaTime % this.framerate);
      this.nextFrame();
    }
  }

  /**
   * Stop the animation
   * @returns {SpriteSheet} This instance for chaining
   */
  stop() {
    this.isPlaying = false;

    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }

    return this;
  }

  /**
   * Pause the animation
   * @returns {SpriteSheet} This instance for chaining
   */
  pause() {
    return this.stop();
  }

  /**
   * Reset to the first frame
   * @returns {SpriteSheet} This instance for chaining
   */
  reset() {
    this.stop();
    this.gotoFrame(0);
    return this;
  }

  /**
   * Toggle play/pause
   * @returns {SpriteSheet} This instance for chaining
   */
  toggle() {
    if (this.isPlaying) {
      this.pause();
    } else {
      this.play();
    }

    return this;
  }

  /**
   * Set the framerate
   * @param {number} fps - Frames per second or milliseconds between frames
   * @param {boolean} [isFPS=false] - If true, value is treated as FPS
   * @returns {SpriteSheet} This instance for chaining
   */
  setFramerate(fps, isFPS = false) {
    this.framerate = isFPS ? 1000 / fps : fps;
    return this;
  }

  /**
   * Load a new sprite sheet image
   * @param {string} imageUrl - URL or data URL
   * @returns {Promise<SpriteSheet>} Resolves when image is loaded
   */
  async loadImage(imageUrl) {
    this.stop();
    this.imageLoaded = false;
    this.loadPromise = this._loadImage(imageUrl);
    await this.loadPromise;
    this.reset();
    return this;
  }

  /**
   * Clear the canvas
   * @returns {SpriteSheet} This instance for chaining
   */
  clear() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    return this;
  }

  /**
   * Destroy the sprite sheet and clean up resources
   */
  destroy() {
    this.stop();
    this.clear();
    this.image = null;
    this.canvas = null;
    this.ctx = null;
  }
}

/**
 * Create a sprite sheet from a file input
 * @param {File} file - Image file
 * @param {Object} options - SpriteSheet options (without image)
 * @returns {Promise<SpriteSheet>} Resolves with SpriteSheet instance
 */
export async function fromFile(file, options = {}) {
  return new Promise((resolve, reject) => {
    if (!file.type.match('image.*')) {
      reject(new Error('File is not an image'));
      return;
    }

    const reader = new FileReader();

    reader.onload = async (e) => {
      try {
        const spriteSheet = new SpriteSheet({
          ...options,
          image: e.target.result
        });
        await spriteSheet.ready();
        resolve(spriteSheet);
      } catch (error) {
        reject(error);
      }
    };

    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };

    reader.readAsDataURL(file);
  });
}

/**
 * SpriteAtlas - Manages multiple sprite animations from a single sprite sheet
 * Perfect for games with many characters/monsters on one texture atlas
 * @class
 */
export class SpriteAtlas {
  /**
   * Create a new SpriteAtlas
   * @param {HTMLCanvasElement|string} canvas - Canvas element or selector
   * @param {string} imageUrl - URL or data URL of the sprite atlas
   */
  constructor(canvas, imageUrl) {
    this.canvas = typeof canvas === 'string' ? document.querySelector(canvas) : canvas;
    this.imageUrl = imageUrl;
    this.sprites = new Map();
    this.currentSprite = null;
    this.image = new Image();
    this.imageLoaded = false;
    this.loadPromise = this._loadImage();
  }

  /**
   * Load the atlas image
   * @private
   */
  _loadImage() {
    return new Promise((resolve, reject) => {
      this.image.onload = () => {
        this.imageLoaded = true;
        this.imageWidth = this.image.width;
        this.imageHeight = this.image.height;
        resolve(this);
      };

      this.image.onerror = () => {
        reject(new Error(`Failed to load atlas: ${this.imageUrl}`));
      };

      this.image.src = this.imageUrl;
    });
  }

  /**
   * Wait for the atlas image to load
   * @returns {Promise<SpriteAtlas>}
   */
  async ready() {
    await this.loadPromise;
    return this;
  }

  /**
   * Define a sprite region in the atlas
   * @param {string} name - Name identifier for this sprite
   * @param {Object} options - Sprite configuration
   * @param {number} options.x - X position in atlas
   * @param {number} options.y - Y position in atlas
   * @param {number} [options.width] - Width of sprite region (auto-detected if not provided)
   * @param {number} [options.height] - Height of sprite region (auto-detected if not provided)
   * @param {number} [options.frameWidth] - Width of each frame (auto-calculated if not provided)
   * @param {number} [options.frameHeight] - Height of each frame (auto-calculated if not provided)
   * @param {number} [options.frames=1] - Number of frames
   * @param {number} [options.rows=1] - Number of rows
   * @param {number} [options.columns] - Number of columns (auto-calculated)
   * @param {number} [options.framerate=60] - Milliseconds between frames
   * @param {number} [options.padding=0] - Padding between frames
   * @param {boolean} [options.loop=true] - Whether to loop
   * @returns {SpriteAtlas} This instance for chaining
   */
  define(name, options) {
    const spriteOptions = {
      canvas: this.canvas,
      image: this.imageUrl,
      regionX: options.x || 0,
      regionY: options.y || 0,
      regionWidth: options.width,
      regionHeight: options.height,
      frameWidth: options.frameWidth,
      frameHeight: options.frameHeight,
      frames: options.frames || 1,
      rows: options.rows || 1,
      columns: options.columns,
      framerate: options.framerate || 60,
      padding: options.padding || 0,
      loop: options.loop !== undefined ? options.loop : true,
      onFrameChange: options.onFrameChange,
      onComplete: options.onComplete
    };

    const sprite = new SpriteSheet(spriteOptions);
    this.sprites.set(name, sprite);

    return this;
  }

  /**
   * Get a sprite by name
   * @param {string} name - Sprite name
   * @returns {SpriteSheet|null}
   */
  get(name) {
    return this.sprites.get(name) || null;
  }

  /**
   * Play a specific sprite animation
   * @param {string} name - Sprite name
   * @returns {SpriteSheet|null}
   */
  async play(name) {
    const sprite = this.get(name);
    if (!sprite) {
      console.warn(`Sprite "${name}" not found in atlas`);
      return null;
    }

    // Stop current sprite if different
    if (this.currentSprite && this.currentSprite !== sprite) {
      this.currentSprite.stop();
    }

    this.currentSprite = sprite;
    await sprite.ready();
    sprite.play();

    return sprite;
  }

  /**
   * Stop all sprite animations
   */
  stopAll() {
    this.sprites.forEach(sprite => sprite.stop());
    this.currentSprite = null;
  }

  /**
   * Get list of all sprite names
   * @returns {string[]}
   */
  list() {
    return Array.from(this.sprites.keys());
  }

  /**
   * Remove a sprite definition
   * @param {string} name - Sprite name
   */
  remove(name) {
    const sprite = this.sprites.get(name);
    if (sprite) {
      sprite.destroy();
      this.sprites.delete(name);
    }
  }

  /**
   * Destroy the atlas and all sprites
   */
  destroy() {
    this.sprites.forEach(sprite => sprite.destroy());
    this.sprites.clear();
    this.image = null;
    this.currentSprite = null;
  }
}

export default SpriteSheet;
