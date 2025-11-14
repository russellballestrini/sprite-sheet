#!/usr/bin/env python3
"""
Analyze and filter animated character sprite sheets from the corpus.
Focus: animated sheets with characters, enemies, players, NPCs, and animals.
"""

import json
import glob
import os
from collections import Counter

def is_animated_character_sheet(sprite):
    """
    Determine if a sprite is an animated character/enemy/player/NPC/animal sheet.
    """
    tags_lower = [t.lower() for t in sprite['tags']]
    title_lower = sprite['title'].lower()
    desc_lower = sprite['description'].lower()

    # Combined text for searching
    all_text = ' '.join(tags_lower + [title_lower, desc_lower])

    # Check if it's animated
    is_animated = any(keyword in all_text for keyword in [
        'animated', 'animation', 'sprite sheet', 'spritesheet',
        'walk', 'run', 'attack', 'idle', 'jump', 'frames', 'frame'
    ])

    # Check if it's a character/enemy/player/NPC/animal
    is_character = any(keyword in all_text for keyword in [
        'character', 'enemy', 'enemies', 'player', 'hero', 'npc',
        'monster', 'creature', 'mob', 'boss', 'villain',
        'animal', 'bird', 'fish', 'dog', 'cat', 'dragon', 'beast',
        'warrior', 'knight', 'mage', 'wizard', 'archer', 'rogue',
        'zombie', 'skeleton', 'alien', 'robot', 'human', 'people',
        'slime', 'ghost', 'demon', 'orc', 'goblin', 'troll',
        'adventurer', 'soldier', 'fighter', 'assassin'
    ])

    # Exclude non-character items
    is_excluded = any(keyword in all_text for keyword in [
        'tileset', 'tile set', 'background', 'icon pack', 'ui',
        'button', 'menu', 'font', 'logo', 'portrait only',
        'static', 'isometric building'
    ]) and not is_character

    return is_animated and is_character and not is_excluded


def categorize_character_type(sprite):
    """Categorize the type of character."""
    tags_lower = [t.lower() for t in sprite['tags']]
    title_lower = sprite['title'].lower()
    all_text = ' '.join(tags_lower + [title_lower])

    if any(word in all_text for word in ['player', 'hero', 'adventurer', 'protagonist']):
        return 'player'
    elif any(word in all_text for word in ['enemy', 'enemies', 'monster', 'mob', 'boss', 'villain']):
        return 'enemy'
    elif any(word in all_text for word in ['npc', 'civilian', 'merchant', 'villager']):
        return 'npc'
    elif any(word in all_text for word in ['animal', 'bird', 'fish', 'creature', 'beast']):
        return 'animal'
    else:
        return 'character'


def main():
    # Load all metadata files
    metadata_files = glob.glob('corpus/metadata/*.json')
    all_sprites = []

    for mf in metadata_files:
        with open(mf) as f:
            all_sprites.append(json.load(f))

    print("="*70)
    print("ANIMATED CHARACTER SPRITE SHEET ANALYSIS")
    print("="*70)
    print(f"\nTotal sprites in corpus: {len(all_sprites)}")

    # Filter for animated character sheets
    animated_chars = []
    for sprite in all_sprites:
        if is_animated_character_sheet(sprite):
            sprite['char_type'] = categorize_character_type(sprite)
            animated_chars.append(sprite)

    print(f"Animated character sheets found: {len(animated_chars)}")

    # Categorize by type
    type_counter = Counter(s['char_type'] for s in animated_chars)
    print("\n" + "="*70)
    print("BREAKDOWN BY TYPE:")
    print("="*70)
    for char_type, count in type_counter.most_common():
        print(f"  {char_type.upper()}: {count}")

    # Size analysis
    sizes = []
    for sprite in animated_chars:
        text = sprite['title'] + ' ' + sprite['description']
        for size in ['8x8', '16x16', '24x24', '32x32', '48x48', '64x64', '128x128']:
            if size in text:
                sizes.append(size)
                break

    if sizes:
        print("\n" + "="*70)
        print("SPRITE SIZES:")
        print("="*70)
        size_counter = Counter(sizes)
        for size, count in size_counter.most_common():
            print(f"  {size}: {count}")

    # Show samples from each category
    print("\n" + "="*70)
    print("SAMPLES BY CATEGORY:")
    print("="*70)

    for char_type in ['player', 'enemy', 'animal', 'npc', 'character']:
        chars_of_type = [s for s in animated_chars if s['char_type'] == char_type]
        if chars_of_type:
            print(f"\n{char_type.upper()} ({len(chars_of_type)} total):")
            for sprite in chars_of_type[:5]:  # Show first 5
                print(f"  • {sprite['title']}")
                print(f"    Tags: {', '.join(sprite['tags'][:6])}")
                print(f"    File: {sprite['local_path']}")
                print()

    # Save filtered list
    output_file = 'corpus/animated_character_sheets.json'
    with open(output_file, 'w') as f:
        json.dump(animated_chars, f, indent=2)

    print("="*70)
    print(f"\nFiltered list saved to: {output_file}")
    print(f"Total animated character sheets: {len(animated_chars)}")
    print("="*70)


if __name__ == '__main__':
    main()
