#!/usr/bin/env python3
"""
Sprite Sheet Grid Detection Tool

Automatically detects frame dimensions in a sprite sheet by analyzing
visual patterns, edges, and repeating structures.

Unix Philosophy: Do one thing well - detect grid dimensions.

Algorithm:
1. Edge Detection: Find strong vertical/horizontal edges
2. Autocorrelation: Detect repeating patterns
3. Color Histogram Analysis: Find frame boundaries by color changes
4. Spacing Analysis: Detect padding between frames

Usage:
    python3 detect_grid.py sprite.png
    python3 detect_grid.py sprite.png --verbose
    python3 detect_grid.py sprite.png --json
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("ERROR: Required libraries not installed.", file=sys.stderr)
    print("Install with: pip install pillow numpy", file=sys.stderr)
    sys.exit(1)


class GridDetector:
    """Detects sprite sheet grid dimensions using computer vision."""

    def __init__(self, image_path):
        self.image = Image.open(image_path)
        self.width, self.height = self.image.size
        self.array = np.array(self.image)

    def detect_edges(self, axis=1):
        """
        Detect edges along an axis (0=vertical, 1=horizontal).
        Returns array of edge strengths.
        """
        # Convert to grayscale
        if len(self.array.shape) == 3:
            gray = np.mean(self.array[:, :, :3], axis=2)
        else:
            gray = self.array

        # Compute gradient along axis
        if axis == 1:  # Horizontal edges (vertical lines)
            gradient = np.abs(np.diff(gray, axis=1))
            edge_strength = np.sum(gradient, axis=0)
        else:  # Vertical edges (horizontal lines)
            gradient = np.abs(np.diff(gray, axis=0))
            edge_strength = np.sum(gradient, axis=1)

        return edge_strength

    def find_peaks(self, signal, min_distance=5):
        """Find peaks in a signal with minimum distance between peaks."""
        peaks = []
        threshold = np.mean(signal) + np.std(signal)

        for i in range(1, len(signal) - 1):
            if signal[i] > threshold:
                # Check if it's a local maximum
                is_peak = True
                for j in range(max(0, i - min_distance), min(len(signal), i + min_distance + 1)):
                    if j != i and signal[j] > signal[i]:
                        is_peak = False
                        break

                if is_peak:
                    # Check minimum distance from existing peaks
                    too_close = False
                    for peak in peaks:
                        if abs(i - peak) < min_distance:
                            too_close = True
                            break

                    if not too_close:
                        peaks.append(i)

        return peaks

    def detect_repeating_pattern(self, edge_strength, min_size=8, max_size=128):
        """Detect repeating pattern size using autocorrelation."""
        best_period = None
        best_score = 0

        for period in range(min_size, min(max_size, len(edge_strength) // 2)):
            # Calculate autocorrelation at this period
            correlation = 0
            count = 0

            for i in range(len(edge_strength) - period):
                correlation += edge_strength[i] * edge_strength[i + period]
                count += 1

            if count > 0:
                score = correlation / count

                if score > best_score:
                    best_score = score
                    best_period = period

        return best_period, best_score

    def detect_grid_dimensions(self):
        """Detect frame width and height."""
        # Detect horizontal edges (for height)
        h_edges = self.detect_edges(axis=0)
        h_peaks = self.find_peaks(h_edges)
        height_period, height_score = self.detect_repeating_pattern(h_edges)

        # Detect vertical edges (for width)
        v_edges = self.detect_edges(axis=1)
        v_peaks = self.find_peaks(v_edges)
        width_period, width_score = self.detect_repeating_pattern(v_edges)

        # Estimate dimensions from peaks
        if len(h_peaks) > 1:
            height_from_peaks = int(np.median(np.diff(h_peaks)))
        else:
            height_from_peaks = height_period

        if len(v_peaks) > 1:
            width_from_peaks = int(np.median(np.diff(v_peaks)))
        else:
            width_from_peaks = width_period

        # Use autocorrelation as primary, peaks as backup
        frame_width = width_period if width_period else width_from_peaks
        frame_height = height_period if height_period else height_from_peaks

        # Calculate rows and columns
        rows = self.height // frame_height if frame_height else 1
        columns = self.width // frame_width if frame_width else 1

        # Detect padding
        padding = self._detect_padding(frame_width, frame_height, columns, rows)

        return {
            'frame_width': frame_width,
            'frame_height': frame_height,
            'columns': columns,
            'rows': rows,
            'padding': padding,
            'total_frames': rows * columns,
            'image_width': self.width,
            'image_height': self.height,
            'confidence': {
                'width': width_score,
                'height': height_score
            }
        }

    def _detect_padding(self, frame_width, frame_height, columns, rows):
        """Detect padding between frames."""
        if not frame_width or not frame_height:
            return 0

        # Check if dimensions divide evenly
        width_remainder = self.width - (frame_width * columns)
        height_remainder = self.height - (frame_height * rows)

        # Padding is likely if there's space left over
        if width_remainder > 0 and columns > 1:
            padding_w = width_remainder // (columns + 1)
        else:
            padding_w = 0

        if height_remainder > 0 and rows > 1:
            padding_h = height_remainder // (rows + 1)
        else:
            padding_h = 0

        # Return the most common padding
        return max(padding_w, padding_h)


def main():
    parser = argparse.ArgumentParser(
        description='Auto-detect sprite sheet grid dimensions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s sprite.png
  %(prog)s character.png --verbose
  %(prog)s atlas.png --json
        """
    )

    parser.add_argument('image', type=str, help='Path to sprite sheet image')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed analysis')
    parser.add_argument('-j', '--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    # Validate image exists
    if not Path(args.image).exists():
        print(f"ERROR: Image file not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    # Run detection
    try:
        detector = GridDetector(args.image)
        result = detector.detect_grid_dimensions()

        if args.json:
            import json
            print(json.dumps(result, indent=2))
        else:
            print(f"\n📐 Grid Detection Results for: {args.image}")
            print("=" * 60)
            print(f"\nImage Dimensions: {result['image_width']}x{result['image_height']} pixels")
            print(f"\nDetected Grid:")
            print(f"  Frame Width:  {result['frame_width']} px")
            print(f"  Frame Height: {result['frame_height']} px")
            print(f"  Columns:      {result['columns']}")
            print(f"  Rows:         {result['rows']}")
            print(f"  Padding:      {result['padding']} px")
            print(f"  Total Frames: {result['total_frames']}")

            if args.verbose:
                print(f"\nConfidence Scores:")
                print(f"  Width:  {result['confidence']['width']:.2f}")
                print(f"  Height: {result['confidence']['height']:.2f}")

            print("\n" + "=" * 60)
            print("\n📋 JavaScript Config:")
            print(f"""
const sprite = new SpriteSheet({{
  canvas: '#canvas',
  image: '{Path(args.image).name}',
  frameWidth: {result['frame_width']},
  frameHeight: {result['frame_height']},
  frames: {result['total_frames']},
  rows: {result['rows']},
  columns: {result['columns']},
  padding: {result['padding']}
}});
""")

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
