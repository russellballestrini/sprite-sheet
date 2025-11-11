#!/usr/bin/env python3
"""
Sprite Grouping Tool

Groups sprites in an atlas by visual similarity using perceptual hashing.
Useful for identifying which sprites are related (same character, different animations).

Unix Philosophy: Do one thing well - group similar sprites.

Algorithm:
1. Extract all frames from the sprite sheet grid
2. Compute perceptual hash for each frame
3. Calculate Hamming distance between hashes
4. Cluster sprites by similarity threshold
5. Output groups of related sprites

Usage:
    python3 group_sprites.py sprite.png --width 32 --height 32
    python3 group_sprites.py atlas.png -w 64 -h 64 --threshold 10
    python3 group_sprites.py atlas.png -w 32 -h 32 --json
"""

import argparse
import sys
from pathlib import Path
from collections import defaultdict

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("ERROR: Required libraries not installed.", file=sys.stderr)
    print("Install with: pip install pillow numpy", file=sys.stderr)
    sys.exit(1)


class SpriteGrouper:
    """Groups sprites by visual similarity using perceptual hashing."""

    def __init__(self, image_path, frame_width=None, frame_height=None):
        self.image = Image.open(image_path)
        self.width, self.height = self.image.size

        # If dimensions not provided, try to detect them
        if frame_width is None or frame_height is None:
            # Import grid detector
            sys.path.insert(0, str(Path(__file__).parent))
            from detect_grid import GridDetector
            detector = GridDetector(image_path)
            result = detector.detect_grid_dimensions()
            self.frame_width = result['frame_width']
            self.frame_height = result['frame_height']
            self.auto_detected = True
        else:
            self.frame_width = frame_width
            self.frame_height = frame_height
            self.auto_detected = False

        self.columns = self.width // self.frame_width
        self.rows = self.height // self.frame_height

    def extract_frames(self):
        """Extract all frames from the sprite sheet."""
        frames = []

        for row in range(self.rows):
            for col in range(self.columns):
                x = col * self.frame_width
                y = row * self.frame_height

                frame = self.image.crop((
                    x, y,
                    x + self.frame_width,
                    y + self.frame_height
                ))

                frames.append({
                    'index': len(frames),
                    'row': row,
                    'col': col,
                    'x': x,
                    'y': y,
                    'image': frame
                })

        return frames

    def perceptual_hash(self, image, hash_size=8):
        """
        Compute perceptual hash of an image.
        Returns a hash that's resistant to minor changes like scaling/compression.
        """
        # Resize to small size
        img = image.resize((hash_size, hash_size), Image.Resampling.LANCZOS)

        # Convert to grayscale
        img = img.convert('L')

        # Get pixel data
        pixels = np.array(img)

        # Compute DCT (Discrete Cosine Transform) approximation
        # For speed, we use a simple average-based hash
        avg = pixels.mean()

        # Create binary hash
        hash_bits = pixels > avg

        return hash_bits

    def hamming_distance(self, hash1, hash2):
        """Calculate Hamming distance between two hashes."""
        return np.sum(hash1 != hash2)

    def group_by_similarity(self, frames, threshold=10):
        """
        Group frames by visual similarity.
        Lower threshold = more strict (only very similar sprites grouped).
        """
        # Compute hashes for all frames
        for frame in frames:
            frame['hash'] = self.perceptual_hash(frame['image'])

        # Group similar frames
        groups = []
        used = set()

        for i, frame1 in enumerate(frames):
            if i in used:
                continue

            # Start a new group
            group = [frame1]
            used.add(i)

            # Find similar frames
            for j, frame2 in enumerate(frames):
                if j in used or i == j:
                    continue

                distance = self.hamming_distance(frame1['hash'], frame2['hash'])

                if distance <= threshold:
                    group.append(frame2)
                    used.add(j)

            groups.append(group)

        return groups

    def detect_animation_sequences(self, groups):
        """
        Detect if groups form animation sequences (consecutive frames in same row).
        """
        for group in groups:
            # Sort by index
            group.sort(key=lambda f: f['index'])

            # Check if consecutive in same row
            is_sequence = True
            if len(group) > 1:
                first_row = group[0]['row']
                for i in range(1, len(group)):
                    if group[i]['row'] != first_row:
                        is_sequence = False
                        break
                    if group[i]['col'] != group[i-1]['col'] + 1:
                        is_sequence = False
                        break
            else:
                is_sequence = False

            # Add metadata
            for frame in group:
                frame['is_sequence'] = is_sequence


def main():
    parser = argparse.ArgumentParser(
        description='Group sprites by visual similarity',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s atlas.png -w 32 -h 32
  %(prog)s sprite-sheet.png --width 64 --height 64 --threshold 15
  %(prog)s mega-atlas.png -w 16 -h 16 --json
  %(prog)s atlas.png  # Auto-detect dimensions
        """
    )

    parser.add_argument('image', type=str, help='Path to sprite sheet image')
    parser.add_argument('-w', '--width', type=int, help='Frame width in pixels (auto-detected if omitted)')
    parser.add_argument('-H', '--height', type=int, help='Frame height in pixels (auto-detected if omitted)')
    parser.add_argument('-t', '--threshold', type=int, default=10,
                       help='Similarity threshold (0-64, lower=stricter, default=10)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed analysis')
    parser.add_argument('-j', '--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    # Validate image exists
    if not Path(args.image).exists():
        print(f"ERROR: Image file not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    # Run grouping
    try:
        grouper = SpriteGrouper(args.image, args.width, args.height)
        frames = grouper.extract_frames()
        groups = grouper.group_by_similarity(frames, args.threshold)
        grouper.detect_animation_sequences(groups)

        # Sort groups by size (largest first)
        groups.sort(key=len, reverse=True)

        if args.json:
            import json
            output = {
                'frame_width': grouper.frame_width,
                'frame_height': grouper.frame_height,
                'auto_detected': grouper.auto_detected,
                'total_frames': len(frames),
                'total_groups': len(groups),
                'groups': []
            }

            for i, group in enumerate(groups):
                group_data = {
                    'id': i,
                    'size': len(group),
                    'is_sequence': group[0].get('is_sequence', False),
                    'frames': [
                        {
                            'index': f['index'],
                            'row': f['row'],
                            'col': f['col'],
                            'x': f['x'],
                            'y': f['y']
                        }
                        for f in group
                    ]
                }
                output['groups'].append(group_data)

            print(json.dumps(output, indent=2))
        else:
            print(f"\n🎨 Sprite Grouping Results for: {args.image}")
            print("=" * 60)

            if grouper.auto_detected:
                print(f"\n📐 Auto-detected dimensions:")
                print(f"  Frame Width:  {grouper.frame_width} px")
                print(f"  Frame Height: {grouper.frame_height} px")
            else:
                print(f"\nFrame Dimensions: {grouper.frame_width}x{grouper.frame_height} pixels")

            print(f"\nGrid Layout: {grouper.rows} rows × {grouper.columns} columns")
            print(f"Total Frames: {len(frames)}")
            print(f"Similarity Threshold: {args.threshold}")
            print(f"\nFound {len(groups)} distinct sprite groups:")

            for i, group in enumerate(groups):
                print(f"\n  Group {i + 1}: {len(group)} frame(s)", end="")

                if group[0].get('is_sequence', False):
                    print(" [Animation Sequence]", end="")

                print()

                if args.verbose or len(group) <= 5:
                    for frame in group:
                        print(f"    Frame {frame['index']:3d}: " +
                              f"Row {frame['row']}, Col {frame['col']} " +
                              f"({frame['x']}, {frame['y']})")
                elif len(group) > 5:
                    print(f"    Frames: ", end="")
                    indices = [f['index'] for f in group]
                    print(', '.join(map(str, indices[:5])) + f", ... ({len(group) - 5} more)")

            print("\n" + "=" * 60)
            print("\n📋 JavaScript Config for Largest Group:")

            if groups:
                largest = groups[0]
                first_frame = largest[0]

                print(f"""
atlas.define('sprite-group-1', {{
  x: {first_frame['x']},
  y: {first_frame['y']},
  width: {grouper.frame_width * len(largest) if largest[0].get('is_sequence', False) else grouper.frame_width},
  height: {grouper.frame_height},
  frames: {len(largest) if largest[0].get('is_sequence', False) else 1},
  rows: 1,
  framerate: 100
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
