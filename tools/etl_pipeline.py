#!/usr/bin/env python3
"""
ETL Pipeline for Sprite Sheet Processing
Extract -> Transform -> Load pipeline with 100% confidence requirement.

Only processes sprite sheets where dimensions can be determined with certainty.
Exports unknown cases for manual review (can be passed to Claude).
"""

import json
import os
import sys
from pathlib import Path
from PIL import Image
import shutil


class SpriteSheetETL:
    """ETL Pipeline for sprite sheet processing."""

    def __init__(self, corpus_dir='corpus'):
        self.corpus_dir = Path(corpus_dir)
        self.processed_dir = self.corpus_dir / 'processed'
        self.sprites_dir = self.corpus_dir / 'extracted_sprites'
        self.review_dir = self.corpus_dir / 'needs_review'
        self.metadata_file = self.corpus_dir / 'sprite_layouts.json'

        # Create directories
        self.processed_dir.mkdir(exist_ok=True)
        self.sprites_dir.mkdir(exist_ok=True)
        self.review_dir.mkdir(exist_ok=True)

        self.stats = {
            'total': 0,
            'processed': 0,
            'needs_review': 0,
            'failed': 0,
            'extracted_frames': 0
        }

    def load_metadata(self):
        """Load sprite layout metadata."""
        if not self.metadata_file.exists():
            print(f"Error: {self.metadata_file} not found!")
            print("Run 'make detect-layout' first.")
            sys.exit(1)

        with open(self.metadata_file) as f:
            return json.load(f)

    def is_100_percent_confident(self, layout):
        """
        Determine if we have 100% confidence in sprite dimensions.

        Criteria for 100% confidence:
        1. Has best_layout detected
        2. Perfect fit (no wasted space) OR
        3. High confidence with text extraction method
        """
        if 'best_layout' not in layout:
            return False

        bl = layout['best_layout']

        # Perfect fit = 100% confidence
        if bl['perfect_fit']:
            return True

        # High confidence text extraction with minimal waste
        if (layout['confidence'] == 'high' and
            bl['method'] == 'text_extraction' and
            bl['waste_percentage'] < 5):
            return True

        return False

    def extract_sprites(self, layout):
        """Extract individual sprites from a sprite sheet."""
        bl = layout['best_layout']
        img_path = Path(layout['file'])

        # Load image
        img = Image.open(img_path)

        # Create output directory for this sprite sheet
        sprite_id = layout['id']
        output_dir = self.sprites_dir / sprite_id
        output_dir.mkdir(exist_ok=True)

        extracted = []

        # Extract each frame
        for frame_idx in range(bl['total_frames']):
            row = frame_idx // bl['cols']
            col = frame_idx % bl['cols']

            x = col * bl['sprite_w']
            y = row * bl['sprite_h']

            # Extract sprite
            sprite = img.crop((x, y, x + bl['sprite_w'], y + bl['sprite_h']))

            # Save sprite
            output_path = output_dir / f"frame_{frame_idx:04d}.png"
            sprite.save(output_path)

            extracted.append({
                'frame': frame_idx,
                'row': row,
                'col': col,
                'x': x,
                'y': y,
                'path': str(output_path.relative_to(self.corpus_dir))
            })

        return extracted

    def create_processed_metadata(self, layout, extracted_frames):
        """Create metadata for processed sprite sheet."""
        bl = layout['best_layout']

        metadata = {
            'id': layout['id'],
            'title': layout['title'],
            'source_file': layout['file'],
            'sprite_dimensions': {
                'width': bl['sprite_w'],
                'height': bl['sprite_h']
            },
            'grid': {
                'cols': bl['cols'],
                'rows': bl['rows'],
                'total_frames': bl['total_frames']
            },
            'detection': {
                'method': bl['method'],
                'confidence': layout['confidence'],
                'perfect_fit': bl['perfect_fit']
            },
            'frames': extracted_frames
        }

        return metadata

    def create_review_package(self, layout):
        """Create review package for unknown cases."""
        review_id = layout['id']
        review_dir = self.review_dir / review_id
        review_dir.mkdir(exist_ok=True)

        # Copy source image
        src_img = Path(layout['file'])
        dst_img = review_dir / src_img.name
        shutil.copy2(src_img, dst_img)

        # Create review metadata
        review_data = {
            'id': layout['id'],
            'title': layout['title'],
            'image_path': str(dst_img.relative_to(self.corpus_dir)),
            'image_dimensions': {
                'width': layout['image_width'],
                'height': layout['image_height']
            },
            'confidence': layout['confidence'],
            'detection_attempts': layout.get('detected_layouts', []),
            'status': 'needs_manual_review',
            'instructions': (
                'Please determine the sprite dimensions for this sheet. '
                'Provide: sprite_width, sprite_height, cols, rows'
            )
        }

        # Save review metadata
        review_file = review_dir / 'review.json'
        with open(review_file, 'w') as f:
            json.dump(review_data, f, indent=2)

        return str(review_file.relative_to(self.corpus_dir))

    def run(self):
        """Run the complete ETL pipeline."""
        print("="*70)
        print("SPRITE SHEET ETL PIPELINE")
        print("="*70)
        print()

        # EXTRACT: Load metadata
        print("📥 EXTRACT: Loading sprite sheet metadata...")
        layouts = self.load_metadata()
        self.stats['total'] = len(layouts)
        print(f"   Loaded {len(layouts)} sprite sheets")

        # TRANSFORM & LOAD: Process each sprite sheet
        print("\n🔄 TRANSFORM & LOAD: Processing sprite sheets...")

        processed_metadata = []
        review_packages = []

        for i, layout in enumerate(layouts):
            sprite_id = layout['id']
            title = layout['title']

            if (i + 1) % 5 == 0 or i == 0:
                print(f"   Progress: {i+1}/{len(layouts)}", flush=True)

            try:
                # Check confidence
                if self.is_100_percent_confident(layout):
                    # PROCESS: Extract sprites
                    extracted = self.extract_sprites(layout)

                    # Create metadata
                    metadata = self.create_processed_metadata(layout, extracted)
                    processed_metadata.append(metadata)

                    self.stats['processed'] += 1
                    self.stats['extracted_frames'] += len(extracted)

                else:
                    # REVIEW: Create review package
                    review_path = self.create_review_package(layout)
                    review_packages.append({
                        'id': sprite_id,
                        'title': title,
                        'review_path': review_path
                    })

                    self.stats['needs_review'] += 1

            except Exception as e:
                print(f"   ✗ Failed: {title} - {e}")
                self.stats['failed'] += 1

        # Save processed metadata
        processed_file = self.processed_dir / 'processed_sprites.json'
        with open(processed_file, 'w') as f:
            json.dump(processed_metadata, f, indent=2)

        # Save review list
        if review_packages:
            review_list_file = self.review_dir / 'review_queue.json'
            with open(review_list_file, 'w') as f:
                json.dump(review_packages, f, indent=2)

        # Print results
        self.print_results()

        return self.stats

    def print_results(self):
        """Print pipeline results."""
        print("\n" + "="*70)
        print("PIPELINE RESULTS")
        print("="*70)

        print(f"\n📊 Statistics:")
        print(f"   Total sprite sheets: {self.stats['total']}")
        print(f"   ✓ Processed (100% confident): {self.stats['processed']}")
        print(f"   ? Needs review: {self.stats['needs_review']}")
        print(f"   ✗ Failed: {self.stats['failed']}")
        print(f"   🎨 Extracted frames: {self.stats['extracted_frames']}")

        if self.stats['processed'] > 0:
            print(f"\n✅ Output:")
            print(f"   Processed metadata: {self.processed_dir / 'processed_sprites.json'}")
            print(f"   Extracted sprites: {self.sprites_dir}/")

        if self.stats['needs_review'] > 0:
            print(f"\n⚠️  Manual Review Required:")
            print(f"   Review queue: {self.review_dir / 'review_queue.json'}")
            print(f"   Review packages: {self.review_dir}/")
            print(f"   → Pass these to Claude for dimension detection")

        # Success rate
        if self.stats['total'] > 0:
            success_rate = (self.stats['processed'] / self.stats['total']) * 100
            print(f"\n📈 Success Rate: {success_rate:.1f}%")

        print("\n" + "="*70)


def main():
    """Main entry point."""
    etl = SpriteSheetETL()
    etl.run()


if __name__ == '__main__':
    main()
