#!/usr/bin/env python3
"""
Sprite Sheet Corpus Fetcher
Fetches public domain sprite sheets from various sources for training data.
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from urllib.parse import urlparse
import urllib.request
import urllib.error
import time
from typing import Dict, List, Optional


class SpriteFetcher:
    """Fetches and organizes public domain sprite sheets"""

    def __init__(self, corpus_dir: str = "corpus", target_count: int = 3000):
        self.corpus_dir = Path(corpus_dir)
        self.raw_dir = self.corpus_dir / "raw"
        self.metadata_dir = self.corpus_dir / "metadata"
        self.target_count = target_count
        self.downloaded_count = 0
        self.skipped_count = 0
        self.failed_count = 0
        self.last_processed = None

        # Create directories if they don't exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        # Count existing files
        self.existing_count = len(list(self.raw_dir.glob('*')))
        print(f"Found {self.existing_count} existing sprites in corpus")

    def download_file(self, url: str, dest_path: Path, timeout: int = 30) -> bool:
        """Download a file from URL to destination path"""
        try:
            print(f"  Downloading: {url}")
            headers = {'User-Agent': 'Mozilla/5.0 (sprite-sheet corpus fetcher)'}
            req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=timeout) as response:
                with open(dest_path, 'wb') as out_file:
                    out_file.write(response.read())

            return True
        except urllib.error.URLError as e:
            print(f"  Failed to download {url}: {e}")
            return False
        except Exception as e:
            print(f"  Error downloading {url}: {e}")
            return False

    def generate_id(self, url: str, title: str) -> str:
        """Generate a unique ID for a sprite sheet"""
        content = f"{url}|{title}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename"""
        ext = Path(filename).suffix.lower()
        return ext if ext else '.png'

    def is_sprite_sheet(self, asset: Dict) -> bool:
        """Determine if an asset is likely a sprite sheet"""
        title_lower = asset.get('title', '').lower()
        desc_lower = asset.get('description', '').lower()
        tags = [tag.lower() for tag in asset.get('tags', [])]

        # Keywords that indicate sprite sheets
        sprite_keywords = [
            'sprite', 'spritesheet', 'sprite sheet', 'animation',
            'character', 'walk', 'run', 'idle', 'attack', 'jump',
            'tile', 'tileset', 'frames', 'animated'
        ]

        # Check if any keyword appears in title, description, or tags
        for keyword in sprite_keywords:
            if keyword in title_lower or keyword in desc_lower or keyword in tags:
                return True

        # Check file extensions in the files list
        if 'files' in asset:
            for file_info in asset.get('files', []):
                filename = file_info.get('name', '').lower()
                if filename.endswith(('.png', '.gif', '.jpg', '.jpeg')):
                    return True

        return False

    def save_metadata(self, sprite_id: str, metadata: Dict) -> None:
        """Save metadata for a sprite sheet"""
        metadata_path = self.metadata_dir / f"{sprite_id}.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, indent=2, fp=f)

    def fetch_from_huggingface_dataset(self, max_items: Optional[int] = None) -> None:
        """
        Fetch sprite sheets from Hugging Face OpenGameArt-CC0 dataset.
        Note: This requires the datasets library to be installed.
        """
        try:
            from datasets import load_dataset
        except ImportError:
            print("ERROR: 'datasets' library not installed.")
            print("Install with: pip install datasets")
            return

        print("\n" + "="*60)
        print("Fetching from Hugging Face OpenGameArt-CC0 dataset")
        print("="*60)

        try:
            # Load the 2D art split from the dataset
            print("Loading dataset... (this may take a few minutes)")
            dataset = load_dataset('nyuuzyou/OpenGameArt-CC0', split='2d_art', streaming=True)

            count = 0
            last_processed_title = None
            for item in dataset:
                if max_items and count >= max_items:
                    break

                # Check if we have enough total sprites (existing + newly downloaded)
                total_sprites = self.existing_count + self.downloaded_count
                if total_sprites >= self.target_count:
                    print(f"\n✓ Reached target count of {self.target_count} sprites!")
                    print(f"   (Existing: {self.existing_count}, Newly downloaded: {self.downloaded_count})")
                    break

                # Check if this is likely a sprite sheet
                if not self.is_sprite_sheet(item):
                    continue

                # Generate unique ID
                sprite_id = self.generate_id(item.get('url', ''), item.get('title', ''))

                title = item.get('title', 'Untitled')
                last_processed_title = title

                total_sprites = self.existing_count + self.downloaded_count
                print(f"\n[{total_sprites + 1}/{self.target_count}] Processing: {title}")

                # Download the first image file we find
                files = item.get('files', [])
                if not files:
                    print("  No files found, skipping...")
                    continue

                downloaded = False
                for file_info in files:
                    file_url = file_info.get('url', '')
                    file_name = file_info.get('name', '')

                    # Only download image files
                    if not any(file_name.lower().endswith(ext) for ext in ['.png', '.gif', '.jpg', '.jpeg']):
                        continue

                    # Create destination path
                    file_ext = self.get_file_extension(file_name)
                    dest_path = self.raw_dir / f"{sprite_id}{file_ext}"

                    # Skip if already downloaded
                    if dest_path.exists():
                        print(f"  ⏭ Already exists: {dest_path.name}")
                        self.skipped_count += 1
                        downloaded = True
                        break

                    # Download the file
                    if self.download_file(file_url, dest_path):
                        # Save metadata
                        metadata = {
                            'id': sprite_id,
                            'source': 'OpenGameArt-CC0',
                            'url': item.get('url', ''),
                            'title': item.get('title', ''),
                            'author': item.get('author', ''),
                            'author_url': item.get('author_url', ''),
                            'post_date': item.get('post_date', ''),
                            'license': 'CC0-1.0',
                            'tags': item.get('tags', []),
                            'description': item.get('description', ''),
                            'file_url': file_url,
                            'file_name': file_name,
                            'local_path': str(dest_path)
                        }
                        self.save_metadata(sprite_id, metadata)

                        self.downloaded_count += 1
                        print(f"  ✓ Downloaded: {dest_path.name}")
                        downloaded = True
                        break
                    else:
                        self.failed_count += 1

                if not downloaded:
                    print("  Failed to download any files for this item")

                count += 1

                # Rate limiting
                time.sleep(0.5)

            # Store last processed title for summary
            self.last_processed = last_processed_title

        except Exception as e:
            print(f"Error fetching from Hugging Face: {e}")

    def fetch_kenney_assets(self) -> None:
        """
        Fetch sprite sheets from Kenney.nl
        Note: This is a placeholder - Kenney requires manual download of packs
        """
        print("\n" + "="*60)
        print("Kenney.nl Assets")
        print("="*60)
        print("Kenney.nl provides excellent CC0 sprite sheets.")
        print("To download Kenney assets:")
        print("1. Visit https://kenney.nl/assets")
        print("2. Download individual packs (free) or all-in-1 bundle ($19.95)")
        print("3. Extract to corpus/raw/ directory")
        print("4. Run this script with --organize-kenney to catalog them")

    def print_summary(self) -> None:
        """Print summary of fetching operation"""
        print("\n" + "="*60)
        print("DOWNLOAD SUMMARY")
        print("="*60)
        print(f"Existing sprites:     {self.existing_count}")
        print(f"Newly downloaded:     {self.downloaded_count}")
        print(f"Skipped (already had): {self.skipped_count}")
        print(f"Failed:               {self.failed_count}")
        print(f"---")
        total_sprites = self.existing_count + self.downloaded_count
        print(f"Total sprites:        {total_sprites}/{self.target_count}")

        if self.last_processed:
            print(f"\nLast item processed:  {self.last_processed}")

        print(f"\nOutput directory: {self.corpus_dir.absolute()}")
        print(f"  - Raw sprites: {self.raw_dir}")
        print(f"  - Metadata: {self.metadata_dir}")


def main():
    parser = argparse.ArgumentParser(
        description='Fetch public domain sprite sheets for corpus'
    )
    parser.add_argument(
        '--target',
        type=int,
        default=3000,
        help='Target number of sprite sheets to fetch (default: 3000)'
    )
    parser.add_argument(
        '--corpus-dir',
        type=str,
        default='corpus',
        help='Directory to store the corpus (default: corpus)'
    )
    parser.add_argument(
        '--source',
        type=str,
        choices=['huggingface', 'kenney', 'all'],
        default='all',
        help='Source to fetch from (default: all)'
    )
    parser.add_argument(
        '--max-items',
        type=int,
        help='Maximum items to process from dataset (for testing)'
    )

    args = parser.parse_args()

    print("="*60)
    print("Sprite Sheet Corpus Fetcher")
    print("="*60)
    print(f"Target: {args.target} sprite sheets")
    print(f"Corpus directory: {args.corpus_dir}")
    print(f"Source: {args.source}")
    print("="*60)

    fetcher = SpriteFetcher(corpus_dir=args.corpus_dir, target_count=args.target)

    if args.source in ['huggingface', 'all']:
        fetcher.fetch_from_huggingface_dataset(max_items=args.max_items)

    if args.source in ['kenney', 'all']:
        fetcher.fetch_kenney_assets()

    fetcher.print_summary()


if __name__ == '__main__':
    main()
