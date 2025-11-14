#!/usr/bin/env python3
"""
Auto-detect sprite sheet layouts.
Analyzes sprite sheets to determine grid dimensions, frame counts, and layout structure.
"""

import json
import glob
import os
import re
from PIL import Image
from collections import Counter
import numpy as np


def extract_sprite_size_from_text(title, description):
    """Extract sprite dimensions from title or description."""
    text = f"{title} {description}".lower()

    # Common patterns: 16x16, 32x32, 64x64, etc.
    patterns = [
        r'(\d+)x(\d+)',
        r'(\d+)\s*x\s*(\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            w, h = int(match.group(1)), int(match.group(2))
            # Filter reasonable sprite sizes (8-512 pixels)
            if 8 <= w <= 512 and 8 <= h <= 512:
                return (w, h)

    return None


def detect_grid_layout(img_width, img_height, sprite_w, sprite_h):
    """Detect grid layout given image and sprite dimensions."""
    cols = int(img_width // sprite_w)
    rows = int(img_height // sprite_h)

    # Check if it divides evenly
    perfect_fit = (img_width % sprite_w == 0) and (img_height % sprite_h == 0)

    # Calculate wasted space
    used_width = int(cols * sprite_w)
    used_height = int(rows * sprite_h)
    wasted_pixels = (img_width - used_width) + (img_height - used_height)
    waste_percentage = float((wasted_pixels / (img_width + img_height)) * 100)

    return {
        'cols': cols,
        'rows': rows,
        'total_frames': int(cols * rows),
        'perfect_fit': bool(perfect_fit),
        'waste_percentage': waste_percentage,
        'used_width': used_width,
        'used_height': used_height
    }


def guess_sprite_dimensions(img_width, img_height):
    """Guess possible sprite dimensions based on common sizes and divisors."""
    common_sizes = [8, 16, 24, 32, 48, 64, 96, 128, 256]
    candidates = []

    for size_w in common_sizes:
        for size_h in common_sizes:
            if img_width >= size_w and img_height >= size_h:
                layout = detect_grid_layout(img_width, img_height, size_w, size_h)

                # Good candidate if low waste and reasonable frame count
                if layout['waste_percentage'] < 20 and 2 <= layout['total_frames'] <= 1000:
                    candidates.append({
                        'sprite_w': int(size_w),
                        'sprite_h': int(size_h),
                        **layout
                    })

    # Sort by perfect fit, then by waste percentage
    candidates.sort(key=lambda x: (not x['perfect_fit'], x['waste_percentage']))

    return candidates[:5]  # Return top 5 candidates


def detect_sprite_boundaries(img):
    """
    Use computer vision to detect sprite boundaries by finding transparent/empty regions.
    Returns detected sprite width and height.
    """
    try:
        # Convert to numpy array
        img_array = np.array(img)

        # Handle different image modes
        if img.mode == 'RGBA':
            alpha = img_array[:, :, 3]
        elif img.mode == 'P' and 'transparency' in img.info:
            # Palette mode with transparency
            alpha = np.array(img.convert('RGBA'))[:, :, 3]
        else:
            # No alpha channel, use brightness
            if len(img_array.shape) == 3:
                gray = np.mean(img_array, axis=2)
            else:
                gray = img_array
            alpha = (gray > 0).astype(np.uint8) * 255

        # Find vertical gaps (columns that are empty)
        vertical_gaps = np.where(np.all(alpha == 0, axis=0))[0]

        # Find horizontal gaps (rows that are empty)
        horizontal_gaps = np.where(np.all(alpha == 0, axis=1))[0]

        # Find repeating patterns in gaps
        if len(vertical_gaps) > 1:
            v_diffs = np.diff(vertical_gaps)
            common_v_spacing = Counter(v_diffs).most_common(1)
            if common_v_spacing:
                sprite_w = common_v_spacing[0][0]
            else:
                sprite_w = None
        else:
            sprite_w = None

        if len(horizontal_gaps) > 1:
            h_diffs = np.diff(horizontal_gaps)
            common_h_spacing = Counter(h_diffs).most_common(1)
            if common_h_spacing:
                sprite_h = common_h_spacing[0][0]
            else:
                sprite_h = None
        else:
            sprite_h = None

        return sprite_w, sprite_h

    except Exception as e:
        return None, None


def analyze_sprite_sheet(sprite_metadata):
    """Analyze a single sprite sheet and detect its layout."""
    result = {
        'id': sprite_metadata['id'],
        'title': sprite_metadata['title'],
        'file': sprite_metadata['local_path'],
        'detected_layouts': [],
        'confidence': 'unknown'
    }

    try:
        # Load image
        img = Image.open(sprite_metadata['local_path'])
        img_width, img_height = img.size

        result['image_width'] = img_width
        result['image_height'] = img_height
        result['image_mode'] = img.mode

        # Method 1: Extract from title/description
        extracted_size = extract_sprite_size_from_text(
            sprite_metadata['title'],
            sprite_metadata['description']
        )

        if extracted_size:
            sprite_w, sprite_h = extracted_size
            layout = detect_grid_layout(img_width, img_height, sprite_w, sprite_h)
            layout['sprite_w'] = int(sprite_w)
            layout['sprite_h'] = int(sprite_h)
            layout['method'] = 'text_extraction'

            result['detected_layouts'].append(layout)

            if layout['perfect_fit']:
                result['confidence'] = 'high'
            elif layout['waste_percentage'] < 10:
                result['confidence'] = 'medium'
            else:
                result['confidence'] = 'low'

        # Method 2: Computer vision detection
        cv_sprite_w, cv_sprite_h = detect_sprite_boundaries(img)
        if cv_sprite_w and cv_sprite_h:
            layout = detect_grid_layout(img_width, img_height, cv_sprite_w, cv_sprite_h)
            layout['sprite_w'] = int(cv_sprite_w)
            layout['sprite_h'] = int(cv_sprite_h)
            layout['method'] = 'computer_vision'
            result['detected_layouts'].append(layout)

        # Method 3: Guess from common sizes
        if not result['detected_layouts']:
            guesses = guess_sprite_dimensions(img_width, img_height)
            for guess in guesses:
                guess['method'] = 'heuristic_guess'
                result['detected_layouts'].append(guess)

            if guesses and guesses[0]['perfect_fit']:
                result['confidence'] = 'medium'
            else:
                result['confidence'] = 'low'

        # Select best layout
        if result['detected_layouts']:
            # Prefer text extraction, then CV, then heuristic
            method_priority = {'text_extraction': 0, 'computer_vision': 1, 'heuristic_guess': 2}
            best = sorted(result['detected_layouts'],
                         key=lambda x: (method_priority.get(x['method'], 999),
                                       not x['perfect_fit'],
                                       x['waste_percentage']))[0]
            result['best_layout'] = best

    except Exception as e:
        result['error'] = str(e)
        result['confidence'] = 'error'

    return result


def main():
    import sys

    # Load animated character sheets
    if os.path.exists('corpus/animated_character_sheets.json'):
        with open('corpus/animated_character_sheets.json') as f:
            sprites = json.load(f)
    else:
        print("Error: Run analyze_animated_characters.py first!")
        sys.exit(1)

    print("="*70)
    print("SPRITE SHEET LAYOUT DETECTION")
    print("="*70)
    print(f"\nAnalyzing {len(sprites)} animated character sprite sheets...")

    results = []

    for i, sprite in enumerate(sprites):
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(sprites)}")

        result = analyze_sprite_sheet(sprite)
        results.append(result)

    # Save results
    output_file = 'corpus/sprite_layouts.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    # Statistics
    print("\n" + "="*70)
    print("LAYOUT DETECTION RESULTS")
    print("="*70)

    confidence_counts = Counter(r['confidence'] for r in results)
    print("\nConfidence Levels:")
    for conf, count in confidence_counts.most_common():
        print(f"  {conf}: {count}")

    # Show some examples
    print("\n" + "="*70)
    print("SAMPLE DETECTED LAYOUTS:")
    print("="*70)

    for conf_level in ['high', 'medium', 'low']:
        conf_results = [r for r in results if r['confidence'] == conf_level]
        if conf_results:
            print(f"\n{conf_level.upper()} CONFIDENCE:")
            for result in conf_results[:3]:
                print(f"\n  • {result['title']}")
                print(f"    Image: {result['image_width']}x{result['image_height']}px")
                if 'best_layout' in result:
                    bl = result['best_layout']
                    print(f"    Detected: {bl['sprite_w']}x{bl['sprite_h']} sprites")
                    print(f"    Grid: {bl['cols']}x{bl['rows']} ({bl['total_frames']} frames)")
                    print(f"    Method: {bl['method']}")
                    print(f"    Perfect fit: {bl['perfect_fit']}")

    print("\n" + "="*70)
    print(f"\nResults saved to: {output_file}")
    print("="*70)


if __name__ == '__main__':
    main()
