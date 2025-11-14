#!/usr/bin/env python3
"""
Split the sprite sheet corpus into training and test sets.
Creates symlinks in the train and test directories pointing to the raw files.
"""

import os
import json
import random
import argparse
from pathlib import Path
from typing import List, Tuple


def load_metadata_files(metadata_dir: Path) -> List[dict]:
    """Load all metadata JSON files"""
    metadata_files = []
    for json_file in metadata_dir.glob("*.json"):
        with open(json_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            metadata_files.append(metadata)
    return metadata_files


def create_splits(
    metadata_list: List[dict],
    train_ratio: float = 0.8,
    seed: int = 42
) -> Tuple[List[dict], List[dict]]:
    """Split metadata into training and test sets"""
    random.seed(seed)
    shuffled = metadata_list.copy()
    random.shuffle(shuffled)

    split_point = int(len(shuffled) * train_ratio)
    train_set = shuffled[:split_point]
    test_set = shuffled[split_point:]

    return train_set, test_set


def create_symlinks(
    metadata_list: List[dict],
    target_dir: Path,
    raw_dir: Path
) -> None:
    """Create symlinks in target directory pointing to raw files"""
    target_dir.mkdir(parents=True, exist_ok=True)

    for metadata in metadata_list:
        sprite_id = metadata['id']
        local_path = Path(metadata['local_path'])

        # Get the file extension
        file_ext = local_path.suffix

        # Create symlink
        symlink_path = target_dir / f"{sprite_id}{file_ext}"
        raw_file_path = raw_dir / local_path.name

        # Remove existing symlink if it exists
        if symlink_path.exists() or symlink_path.is_symlink():
            symlink_path.unlink()

        # Create relative symlink
        relative_path = os.path.relpath(raw_file_path, target_dir)
        symlink_path.symlink_to(relative_path)


def save_manifest(
    metadata_list: List[dict],
    output_path: Path
) -> None:
    """Save a manifest file listing all sprites in the set"""
    manifest = {
        'count': len(metadata_list),
        'sprites': [
            {
                'id': m['id'],
                'title': m['title'],
                'author': m['author'],
                'tags': m['tags'],
                'source': m['source'],
                'license': m['license']
            }
            for m in metadata_list
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description='Split sprite sheet corpus into train/test sets'
    )
    parser.add_argument(
        '--corpus-dir',
        type=str,
        default='corpus',
        help='Corpus directory (default: corpus)'
    )
    parser.add_argument(
        '--train-ratio',
        type=float,
        default=0.8,
        help='Training set ratio (default: 0.8 = 80%%)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )

    args = parser.parse_args()

    corpus_dir = Path(args.corpus_dir)
    metadata_dir = corpus_dir / 'metadata'
    raw_dir = corpus_dir / 'raw'
    train_dir = corpus_dir / 'train'
    test_dir = corpus_dir / 'test'

    print("="*60)
    print("Sprite Sheet Corpus Splitter")
    print("="*60)
    print(f"Corpus directory: {corpus_dir.absolute()}")
    print(f"Train ratio: {args.train_ratio * 100:.0f}%")
    print(f"Test ratio: {(1 - args.train_ratio) * 100:.0f}%")
    print(f"Random seed: {args.seed}")
    print("="*60)

    # Load all metadata
    print("\nLoading metadata...")
    metadata_list = load_metadata_files(metadata_dir)
    print(f"Found {len(metadata_list)} sprite sheets")

    if len(metadata_list) == 0:
        print("ERROR: No metadata files found!")
        print(f"Make sure you've run fetch_sprites.py first.")
        return

    # Create train/test split
    print("\nCreating train/test split...")
    train_set, test_set = create_splits(
        metadata_list,
        train_ratio=args.train_ratio,
        seed=args.seed
    )

    print(f"Training set: {len(train_set)} sprites ({len(train_set)/len(metadata_list)*100:.1f}%)")
    print(f"Test set: {len(test_set)} sprites ({len(test_set)/len(metadata_list)*100:.1f}%)")

    # Create symlinks
    print("\nCreating symlinks for training set...")
    create_symlinks(train_set, train_dir, raw_dir)

    print("Creating symlinks for test set...")
    create_symlinks(test_set, test_dir, raw_dir)

    # Save manifests
    print("\nSaving manifests...")
    save_manifest(train_set, train_dir / 'manifest.json')
    save_manifest(test_set, test_dir / 'manifest.json')

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total sprites: {len(metadata_list)}")
    print(f"Training set: {len(train_set)} sprites")
    print(f"Test set: {len(test_set)} sprites")
    print(f"\nTraining directory: {train_dir.absolute()}")
    print(f"Test directory: {test_dir.absolute()}")
    print(f"\nManifests saved:")
    print(f"  - {train_dir / 'manifest.json'}")
    print(f"  - {test_dir / 'manifest.json'}")
    print("="*60)


if __name__ == '__main__':
    main()
