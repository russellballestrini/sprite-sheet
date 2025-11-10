import terser from '@rollup/plugin-terser';

export default [
  // ES Module build
  {
    input: 'src/SpriteSheet.js',
    output: {
      file: 'dist/sprite-sheet.js',
      format: 'es',
      sourcemap: true
    }
  },
  // Minified ES Module build
  {
    input: 'src/SpriteSheet.js',
    output: {
      file: 'dist/sprite-sheet.min.js',
      format: 'es',
      sourcemap: true,
      plugins: [terser()]
    }
  },
  // UMD build for browsers (no module support)
  {
    input: 'src/SpriteSheet.js',
    output: {
      file: 'dist/sprite-sheet.umd.js',
      format: 'umd',
      name: 'SpriteSheet',
      sourcemap: true
    }
  },
  // CommonJS build
  {
    input: 'src/SpriteSheet.js',
    output: {
      file: 'dist/sprite-sheet.cjs',
      format: 'cjs',
      sourcemap: true,
      exports: 'named'
    }
  }
];
