#!/usr/bin/env python3
"""
Multi-License Sprite Sheet Corpus Fetcher
Fetches sprite sheets and 3D models from various licenses, organizing by license type.

Directory Structure:
  corpus/
    cc0/          - CC0 (Public Domain) - trainable
    cc-by/        - CC-BY (Attribution) - trainable with attribution
    cc-by-sa/     - CC-BY-SA (Attribution + ShareAlike) - trainable with attribution
    gpl/          - GPL licenses - NOT trainable, kept for reference
    3d/           - 3D models (all licenses) - for 360° screenshot generation
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
import urllib.request
import urllib.error
import time
from typing import Dict, List, Optional, Tuple


class MultiLicenseFetcher:
    """Fetches and organizes sprite sheets by license type"""

    # Dataset configurations: (hf_dataset_name, license_name, is_trainable)
    DATASETS = {
        'cc0': {
            'hf_name': 'nyuuzyou/OpenGameArt-CC0',
            'license': 'CC0-1.0',
            'trainable': True,
            'description': 'Public Domain - No attribution required'
        },
        'cc-by': {
            'hf_name': 'nyuuzyou/OpenGameArt-CC-BY-3.0',
            'license': 'CC-BY-3.0',
            'trainable': True,
            'description': 'Attribution required'
        },
        'cc-by-sa': {
            'hf_name': 'nyuuzyou/OpenGameArt-CC-BY-SA-3.0',
            'license': 'CC-BY-SA-3.0',
            'trainable': True,
            'description': 'Attribution + ShareAlike'
        },
        'gpl': {
            'hf_name': 'nyuuzyou/OpenGameArt-GPL-3.0',
            'license': 'GPL-3.0',
            'trainable': False,
            'description': 'GPL - Reference only, not for training'
        }
    }

    def __init__(self, corpus_dir: str = "corpus"):
        self.corpus_dir = Path(corpus_dir)
        self.stats = {}

        # Initialize stats for each license
        for license_key in self.DATASETS.keys():
            self.stats[license_key] = {
                'existing_2d': 0,
                'existing_3d': 0,
                'downloaded_2d': 0,
                'downloaded_3d': 0,
                'skipped': 0,
                'failed': 0,
                'last_processed': None
            }

        # Create directory structure
        self._setup_directories()

    def _setup_directories(self):
        """Create organized directory structure"""
        for license_key in self.DATASETS.keys():
            # 2D assets
            (self.corpus_dir / license_key / "raw").mkdir(parents=True, exist_ok=True)
            (self.corpus_dir / license_key / "metadata").mkdir(parents=True, exist_ok=True)

            # Count existing files
            existing_2d = len(list((self.corpus_dir / license_key / "raw").glob('*')))
            self.stats[license_key]['existing_2d'] = existing_2d

        # 3D models (separate, organized by license)
        for license_key in self.DATASETS.keys():
            (self.corpus_dir / "3d" / license_key / "raw").mkdir(parents=True, exist_ok=True)
            (self.corpus_dir / "3d" / license_key / "metadata").mkdir(parents=True, exist_ok=True)

            existing_3d = len(list((self.corpus_dir / "3d" / license_key / "raw").glob('*')))
            self.stats[license_key]['existing_3d'] = existing_3d

    def generate_id(self, url: str, title: str) -> str:
        """Generate a unique ID for an asset"""
        content = f"{url}|{title}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename"""
        ext = Path(filename).suffix.lower()
        return ext if ext else '.png'

    def is_2d_asset(self, asset: Dict) -> bool:
        """Determine if an asset is 2D (sprite sheet, texture, etc)"""
        title_lower = asset.get('title', '').lower()
        desc_lower = asset.get('description', '').lower()
        tags = [tag.lower() for tag in asset.get('tags', [])]

        # Keywords for 2D assets
        keywords_2d = [
            'sprite', 'spritesheet', 'sprite sheet', 'animation',
            'character', 'walk', 'run', 'idle', 'attack', 'jump',
            'tile', 'tileset', 'frames', 'animated', 'texture',
            'icon', 'ui', 'pixel art', '2d', 'background'
        ]

        for keyword in keywords_2d:
            if keyword in title_lower or keyword in desc_lower or keyword in tags:
                return True

        # Check file extensions
        if 'files' in asset:
            for file_info in asset.get('files', []):
                filename = file_info.get('name', '').lower()
                if filename.endswith(('.png', '.gif', '.jpg', '.jpeg')):
                    return True

        return False

    def is_3d_asset(self, asset: Dict) -> bool:
        """Determine if an asset is 3D model"""
        title_lower = asset.get('title', '').lower()
        desc_lower = asset.get('description', '').lower()
        tags = [tag.lower() for tag in asset.get('tags', [])]

        # Keywords for 3D assets
        keywords_3d = [
            '3d', 'model', 'blend', 'blender', 'obj', 'fbx',
            'mesh', 'lowpoly', 'low poly', 'character model'
        ]

        for keyword in keywords_3d:
            if keyword in title_lower or keyword in desc_lower or keyword in tags:
                # Check for 3D file extensions
                if 'files' in asset:
                    for file_info in asset.get('files', []):
                        filename = file_info.get('name', '').lower()
                        if filename.endswith(('.blend', '.obj', '.fbx', '.dae', '.gltf', '.glb')):
                            return True

        return False

    def download_file(self, url: str, dest_path: Path, timeout: int = 30) -> bool:
        """Download a file from URL to destination path"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (sprite-sheet corpus fetcher)'}
            req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=timeout) as response:
                with open(dest_path, 'wb') as out_file:
                    out_file.write(response.read())

            return True
        except Exception as e:
            print(f"  ✗ Download failed: {e}")
            return False

    def save_metadata(self, metadata_dir: Path, asset_id: str, metadata: Dict) -> None:
        """Save metadata for an asset"""
        metadata_path = metadata_dir / f"{asset_id}.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, indent=2, fp=f)

    def fetch_dataset(self, license_key: str, split: str, target_count: Optional[int] = None) -> None:
        """Fetch assets from a specific dataset and split"""
        try:
            from datasets import load_dataset
        except ImportError:
            print("ERROR: 'datasets' library not installed.")
            print("Install with: pip install datasets")
            return

        config = self.DATASETS[license_key]
        dataset_name = config['hf_name']

        print("\n" + "="*70)
        print(f"Fetching: {dataset_name} - {split}")
        print(f"License: {config['license']} ({config['description']})")
        print(f"Trainable: {'Yes' if config['trainable'] else 'No (reference only)'}")
        print("="*70)

        try:
            dataset = load_dataset(dataset_name, split=split, streaming=True)

            count = 0
            for item in dataset:
                # Check target
                if target_count:
                    if split == '2d_art':
                        total = self.stats[license_key]['existing_2d'] + self.stats[license_key]['downloaded_2d']
                    elif split == '3d_art':
                        total = self.stats[license_key]['existing_3d'] + self.stats[license_key]['downloaded_3d']
                    else:
                        total = self.stats[license_key]['existing_2d'] + self.stats[license_key]['downloaded_2d']

                    if total >= target_count:
                        print(f"✓ Reached target of {target_count} for {license_key}/{split}")
                        break

                title = item.get('title', 'Untitled')
                self.stats[license_key]['last_processed'] = title

                # Determine asset type and destination
                is_3d = self.is_3d_asset(item) and split == '3d_art'
                is_2d = self.is_2d_asset(item) and split == '2d_art'

                if not (is_2d or is_3d):
                    continue

                # Set directories based on type
                if is_3d:
                    raw_dir = self.corpus_dir / "3d" / license_key / "raw"
                    metadata_dir = self.corpus_dir / "3d" / license_key / "metadata"
                    total = self.stats[license_key]['existing_3d'] + self.stats[license_key]['downloaded_3d']
                else:
                    raw_dir = self.corpus_dir / license_key / "raw"
                    metadata_dir = self.corpus_dir / license_key / "metadata"
                    total = self.stats[license_key]['existing_2d'] + self.stats[license_key]['downloaded_2d']

                asset_id = self.generate_id(item.get('url', ''), title)

                if target_count:
                    print(f"\n[{total + 1}/{target_count}] {license_key}/{split}: {title}")
                else:
                    print(f"\n[{total + 1}] {license_key}/{split}: {title}")

                # Download files
                files = item.get('files', [])
                if not files:
                    continue

                downloaded = False
                for file_info in files:
                    file_url = file_info.get('url', '')
                    file_name = file_info.get('name', '')

                    # Filter by file type
                    if is_3d:
                        valid_exts = ('.blend', '.obj', '.fbx', '.dae', '.gltf', '.glb')
                    else:
                        valid_exts = ('.png', '.gif', '.jpg', '.jpeg')

                    if not any(file_name.lower().endswith(ext) for ext in valid_exts):
                        continue

                    # Create destination path
                    file_ext = self.get_file_extension(file_name)
                    dest_path = raw_dir / f"{asset_id}{file_ext}"

                    # Skip if exists
                    if dest_path.exists():
                        print(f"  ⏭ Already exists")
                        self.stats[license_key]['skipped'] += 1
                        downloaded = True
                        break

                    # Download
                    if self.download_file(file_url, dest_path):
                        # Save metadata
                        metadata = {
                            'id': asset_id,
                            'source': dataset_name,
                            'url': item.get('url', ''),
                            'title': title,
                            'author': item.get('author', ''),
                            'author_url': item.get('author_url', ''),
                            'post_date': item.get('post_date', ''),
                            'license': config['license'],
                            'trainable': config['trainable'],
                            'tags': item.get('tags', []),
                            'description': item.get('description', ''),
                            'file_url': file_url,
                            'file_name': file_name,
                            'local_path': str(dest_path),
                            'asset_type': '3d' if is_3d else '2d'
                        }
                        self.save_metadata(metadata_dir, asset_id, metadata)

                        if is_3d:
                            self.stats[license_key]['downloaded_3d'] += 1
                        else:
                            self.stats[license_key]['downloaded_2d'] += 1

                        print(f"  ✓ Downloaded")
                        downloaded = True
                        break
                    else:
                        self.stats[license_key]['failed'] += 1

                if not downloaded:
                    print(f"  ✗ Failed to download")

                count += 1
                time.sleep(0.3)  # Rate limiting

        except Exception as e:
            print(f"Error fetching {dataset_name}/{split}: {e}")

    def print_summary(self):
        """Print comprehensive summary"""
        print("\n" + "="*70)
        print("MULTI-LICENSE DOWNLOAD SUMMARY")
        print("="*70)

        for license_key, config in self.DATASETS.items():
            stats = self.stats[license_key]
            print(f"\n{license_key.upper()} ({config['license']})")
            print(f"  {config['description']}")
            print(f"  Trainable: {'Yes' if config['trainable'] else 'No'}")
            print(f"  2D Assets:")
            print(f"    Existing:        {stats['existing_2d']}")
            print(f"    Downloaded:      {stats['downloaded_2d']}")
            print(f"    Total:           {stats['existing_2d'] + stats['downloaded_2d']}")
            print(f"  3D Assets:")
            print(f"    Existing:        {stats['existing_3d']}")
            print(f"    Downloaded:      {stats['downloaded_3d']}")
            print(f"    Total:           {stats['existing_3d'] + stats['downloaded_3d']}")
            print(f"  Skipped:           {stats['skipped']}")
            print(f"  Failed:            {stats['failed']}")
            if stats['last_processed']:
                print(f"  Last processed:    {stats['last_processed'][:60]}")

        # Grand totals
        total_2d = sum(s['existing_2d'] + s['downloaded_2d'] for s in self.stats.values())
        total_3d = sum(s['existing_3d'] + s['downloaded_3d'] for s in self.stats.values())
        total_trainable_2d = sum(
            s['existing_2d'] + s['downloaded_2d']
            for k, s in self.stats.items()
            if self.DATASETS[k]['trainable']
        )

        print("\n" + "="*70)
        print("GRAND TOTALS")
        print("="*70)
        print(f"Total 2D assets:       {total_2d}")
        print(f"  Trainable:           {total_trainable_2d}")
        print(f"Total 3D assets:       {total_3d}")
        print(f"Total all assets:      {total_2d + total_3d}")
        print(f"\nCorpus directory:      {self.corpus_dir.absolute()}")


def main():
    parser = argparse.ArgumentParser(
        description='Fetch sprite sheets and 3D models organized by license'
    )
    parser.add_argument(
        '--corpus-dir',
        type=str,
        default='corpus',
        help='Base corpus directory (default: corpus)'
    )
    parser.add_argument(
        '--licenses',
        nargs='+',
        choices=['cc0', 'cc-by', 'cc-by-sa', 'gpl', 'all'],
        default=['all'],
        help='Which licenses to fetch (default: all)'
    )
    parser.add_argument(
        '--splits',
        nargs='+',
        choices=['2d_art', '3d_art', 'all'],
        default=['all'],
        help='Which splits to fetch (default: all)'
    )
    parser.add_argument(
        '--target-per-license',
        type=int,
        help='Target count per license/split combination'
    )

    args = parser.parse_args()

    # Expand 'all'
    if 'all' in args.licenses:
        licenses = ['cc0', 'cc-by', 'cc-by-sa', 'gpl']
    else:
        licenses = args.licenses

    if 'all' in args.splits:
        splits = ['2d_art', '3d_art']
    else:
        splits = args.splits

    print("="*70)
    print("MULTI-LICENSE SPRITE SHEET & 3D MODEL FETCHER")
    print("="*70)
    print(f"Licenses: {', '.join(licenses)}")
    print(f"Splits: {', '.join(splits)}")
    print(f"Corpus directory: {args.corpus_dir}")
    print("="*70)

    fetcher = MultiLicenseFetcher(corpus_dir=args.corpus_dir)

    # Fetch each combination
    for license_key in licenses:
        for split in splits:
            fetcher.fetch_dataset(license_key, split, target_count=args.target_per_license)

    fetcher.print_summary()


if __name__ == '__main__':
    main()
