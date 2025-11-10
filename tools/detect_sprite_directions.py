#!/usr/bin/env python3
"""
Sprite Sheet Direction Detection Tool

Analyzes a sprite sheet to automatically determine which row corresponds to
which direction (up, down, left, right) based on pixel analysis.

Algorithm:
1. Optical Flow Analysis: Detect apparent motion direction in animation frames
2. Symmetry Analysis: Detect left/right facing based on horizontal symmetry
3. Center of Mass: Track center of mass movement across frames
4. Edge Detection: Analyze which edges show most activity

Usage:
    python3 detect_sprite_directions.py sprite.png --width 16 --height 18 --frames 3 --rows 4
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("ERROR: Required libraries not installed.")
    print("Install with: pip install pillow numpy")
    sys.exit(1)


class SpriteDirectionDetector:
    """Detects sprite animation directions using computer vision techniques."""

    def __init__(self, image_path, frame_width, frame_height, frames_per_row, num_rows):
        self.image = Image.open(image_path)
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.frames_per_row = frames_per_row
        self.num_rows = num_rows

    def extract_row(self, row_index):
        """Extract all frames from a specific row."""
        y = row_index * self.frame_height
        frames = []

        for i in range(self.frames_per_row):
            x = i * self.frame_width
            frame = self.image.crop((x, y, x + self.frame_width, y + self.frame_height))
            frames.append(np.array(frame))

        return frames

    def detect_vertical_motion(self, frames):
        """
        Detect vertical motion by analyzing center of mass movement.
        Returns: positive for downward, negative for upward, 0 for horizontal.
        """
        if len(frames) < 2:
            return 0

        centers_y = []
        for frame in frames:
            # Convert to grayscale if color
            if len(frame.shape) == 3:
                gray = np.mean(frame[:, :, :3], axis=2)
            else:
                gray = frame

            # Find center of mass (weighted by pixel intensity)
            y_coords, x_coords = np.mgrid[0:gray.shape[0], 0:gray.shape[1]]
            total_mass = np.sum(gray)

            if total_mass > 0:
                center_y = np.sum(y_coords * gray) / total_mass
                centers_y.append(center_y)

        # Calculate average vertical movement
        if len(centers_y) < 2:
            return 0

        movements = np.diff(centers_y)
        return np.mean(movements)

    def detect_horizontal_asymmetry(self, frames):
        """
        Detect if sprite is facing left or right based on horizontal asymmetry.
        Returns: positive for right-facing, negative for left-facing.
        """
        asymmetries = []

        for frame in frames:
            # Convert to grayscale if color
            if len(frame.shape) == 3:
                gray = np.mean(frame[:, :, :3], axis=2)
            else:
                gray = frame

            # Compare left and right halves
            mid = gray.shape[1] // 2
            left_half = gray[:, :mid]
            right_half = np.fliplr(gray[:, mid:])

            # Pad if uneven
            min_width = min(left_half.shape[1], right_half.shape[1])
            left_half = left_half[:, :min_width]
            right_half = right_half[:, :min_width]

            # Calculate asymmetry (positive = right-biased, negative = left-biased)
            left_mass = np.sum(left_half)
            right_mass = np.sum(right_half)

            if left_mass + right_mass > 0:
                asymmetry = (right_mass - left_mass) / (right_mass + left_mass)
                asymmetries.append(asymmetry)

        return np.mean(asymmetries) if asymmetries else 0

    def detect_motion_amount(self, frames):
        """
        Detect overall amount of motion/change between frames.
        Higher values indicate more animated motion.
        """
        if len(frames) < 2:
            return 0

        differences = []
        for i in range(len(frames) - 1):
            frame1 = frames[i]
            frame2 = frames[i + 1]

            # Convert to grayscale
            if len(frame1.shape) == 3:
                gray1 = np.mean(frame1[:, :, :3], axis=2)
                gray2 = np.mean(frame2[:, :, :3], axis=2)
            else:
                gray1 = frame1
                gray2 = frame2

            # Calculate pixel differences
            diff = np.abs(gray1.astype(float) - gray2.astype(float))
            differences.append(np.mean(diff))

        return np.mean(differences)

    def analyze_row(self, row_index):
        """Analyze a row and return motion characteristics."""
        frames = self.extract_row(row_index)

        vertical_motion = self.detect_vertical_motion(frames)
        horizontal_asymmetry = self.detect_horizontal_asymmetry(frames)
        motion_amount = self.detect_motion_amount(frames)

        return {
            'row': row_index,
            'vertical_motion': vertical_motion,
            'horizontal_asymmetry': horizontal_asymmetry,
            'motion_amount': motion_amount
        }

    def detect_all_directions(self):
        """Analyze all rows and determine directions."""
        analyses = []

        for i in range(self.num_rows):
            analysis = self.analyze_row(i)
            analyses.append(analysis)

        # Determine directions based on analysis
        directions = {}

        # Find down (highest positive vertical motion)
        down_row = max(analyses, key=lambda x: x['vertical_motion'])
        directions['down'] = down_row['row']

        # Find up (most negative vertical motion)
        up_row = min(analyses, key=lambda x: x['vertical_motion'])
        directions['up'] = up_row['row']

        # Find left and right from remaining rows
        remaining = [a for a in analyses if a['row'] not in [directions['down'], directions['up']]]

        if len(remaining) >= 2:
            # Right-facing has positive horizontal asymmetry
            right_row = max(remaining, key=lambda x: x['horizontal_asymmetry'])
            directions['right'] = right_row['row']

            # Left is the other one
            left_row = [a for a in remaining if a['row'] != directions['right']][0]
            directions['left'] = left_row['row']
        elif len(remaining) == 1:
            # Only one horizontal direction, guess based on asymmetry
            if remaining[0]['horizontal_asymmetry'] > 0:
                directions['right'] = remaining[0]['row']
            else:
                directions['left'] = remaining[0]['row']

        return directions, analyses


def main():
    parser = argparse.ArgumentParser(
        description='Detect sprite sheet animation directions automatically',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s sprite.png -w 16 -h 18 -f 3 -r 4
  %(prog)s Green-Cap.png --width 16 --height 18 --frames 3 --rows 4
  %(prog)s character.png -w 32 -h 32 -f 4 -r 4 --verbose
        """
    )

    parser.add_argument('image', type=str, help='Path to sprite sheet image')
    parser.add_argument('-w', '--width', type=int, required=True, help='Frame width in pixels')
    parser.add_argument('-H', '--height', type=int, required=True, help='Frame height in pixels')
    parser.add_argument('-f', '--frames', type=int, required=True, help='Number of frames per row')
    parser.add_argument('-r', '--rows', type=int, required=True, help='Number of rows')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed analysis')
    parser.add_argument('-j', '--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    # Validate image exists
    if not Path(args.image).exists():
        print(f"ERROR: Image file not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    # Run detection
    try:
        detector = SpriteDirectionDetector(
            args.image,
            args.width,
            args.height,
            args.frames,
            args.rows
        )

        directions, analyses = detector.detect_all_directions()

        if args.json:
            import json
            output = {
                'directions': directions,
                'analyses': analyses if args.verbose else None
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"\n🎮 Sprite Direction Detection Results for: {args.image}")
            print("=" * 60)
            print(f"\nDetected direction mapping:")
            for direction in ['down', 'left', 'right', 'up']:
                if direction in directions:
                    print(f"  {direction:>6}: Row {directions[direction]}")

            if args.verbose:
                print(f"\nDetailed Analysis:")
                print("-" * 60)
                for analysis in analyses:
                    print(f"\nRow {analysis['row']}:")
                    print(f"  Vertical Motion:      {analysis['vertical_motion']:>8.3f} " +
                          f"({'down' if analysis['vertical_motion'] > 0 else 'up' if analysis['vertical_motion'] < 0 else 'neutral'})")
                    print(f"  Horizontal Asymmetry: {analysis['horizontal_asymmetry']:>8.3f} " +
                          f"({'right' if analysis['horizontal_asymmetry'] > 0 else 'left' if analysis['horizontal_asymmetry'] < 0 else 'centered'})")
                    print(f"  Motion Amount:        {analysis['motion_amount']:>8.3f}")

            print("\n" + "=" * 60)
            print("\n📋 JavaScript Config:")
            print(f"""
const animations = {{
  down: {{ regionY: {directions.get('down', 0)} * frameHeight }},
  left: {{ regionY: {directions.get('left', 1)} * frameHeight }},
  right: {{ regionY: {directions.get('right', 2)} * frameHeight }},
  up: {{ regionY: {directions.get('up', 3)} * frameHeight }}
}};
""")

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
