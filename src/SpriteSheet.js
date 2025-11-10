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
   * @param {number} [options.frameWidth=100] - Width of each frame
   * @param {number} [options.frameHeight=100] - Height of each frame
   * @param {number} [options.frames=1] - Total number of frames
   * @param {number} [options.framerate=60] - Milliseconds between frames
   * @param {number} [options.padding=0] - Padding between frames
   * @param {number} [options.rows=1] - Number of rows in sprite sheet
   * @param {number} [options.columns=0] - Number of columns (auto-calculated if 0)
   * @param {boolean} [options.loop=true] - Whether to loop the animation
   * @param {Function} [options.onFrameChange] - Callback when frame changes
   * @param {Function} [options.onComplete] - Callback when animation completes
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

    // Sprite sheet parameters
    this.frameWidth = options.frameWidth || 100;
    this.frameHeight = options.frameHeight || 100;
    this.totalFrames = options.frames || 1;
    this.framerate = options.framerate || 60;
    this.padding = options.padding || 0;
    this.rows = options.rows || 1;
    this.columns = options.columns || Math.ceil(this.totalFrames / this.rows);
    this.loop = options.loop !== undefined ? options.loop : true;

    // Callbacks
    this.onFrameChange = options.onFrameChange || null;
    this.onComplete = options.onComplete || null;

    // Animation state
    this.currentFrame = 0;
    this.isPlaying = false;
    this.animationId = null;
    this.lastFrameTime = 0;

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
        resolve(this);
      };

      this.image.onerror = () => {
        reject(new Error(`Failed to load image: ${imageUrl}`));
      };

      this.image.src = imageUrl;
    });
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
      x: col * (this.frameWidth + this.padding) + this.padding,
      y: row * (this.frameHeight + this.padding) + this.padding
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

export default SpriteSheet;
