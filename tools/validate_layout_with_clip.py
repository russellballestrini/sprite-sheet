#!/usr/bin/env python3
"""
Validate sprite sheet layouts using CLIP.
Uses CLIP to verify that detected sprite dimensions are correct by checking
if the subject is centered in the extracted frame.
"""

import json
import torch
from PIL import Image
import numpy as np
from pathlib import Path
import sys


def load_clip_model():
    """Load CLIP model for image analysis."""
    try:
        import clip
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model, preprocess = clip.load("ViT-B/32", device=device)
        return model, preprocess, device
    except ImportError:
        print("Error: CLIP not installed. Run: pip install git+https://github.com/openai/CLIP.git")
        sys.exit(1)


def extract_sample_frames(img_path, sprite_w, sprite_h, cols, rows, num_samples=4):
    """Extract sample frames from different positions in the sprite sheet."""
    img = Image.open(img_path)
    samples = []

    total_frames = cols * rows
    if total_frames == 0:
        return []

    # Sample frames from different positions
    # Start, middle, and end positions
    sample_indices = [
        0,  # First frame
        total_frames // 4,  # Quarter way
        total_frames // 2,  # Middle
        total_frames - 1  # Last frame
    ][:min(num_samples, total_frames)]

    for frame_idx in sample_indices:
        row = frame_idx // cols
        col = frame_idx % cols

        x = col * sprite_w
        y = row * sprite_h

        # Extract frame
        frame = img.crop((x, y, x + sprite_w, y + sprite_h))

        samples.append({
            'frame_idx': frame_idx,
            'position': (row, col),
            'image': frame
        })

    return samples


def check_subject_centered(frame_img, model, preprocess, device, sprite_dims=None):
    """
    Use CLIP to check if subject is centered in the frame.
    Returns a confidence score (0-1) that the subject is properly framed.

    Args:
        frame_img: PIL Image of the extracted frame
        sprite_dims: Optional dict with 'sprite_w', 'sprite_h' from detection
    """
    # Prepare image
    image = preprocess(frame_img).unsqueeze(0).to(device)

    # Text prompts - use detected dimensions if available
    if sprite_dims:
        size_hint = f"{sprite_dims['sprite_w']}x{sprite_dims['sprite_h']} pixel"
    else:
        size_hint = ""

    text_prompts = [
        f"a {size_hint} character sprite centered in frame",
        f"a complete {size_hint} character in the center",
        "an empty frame",
        "a cropped character at the edge",
        "partial sprite cut off at frame boundary"
    ]

    text = torch.cat([clip.tokenize(prompt) for prompt in text_prompts]).to(device)

    # Get similarity scores
    with torch.no_grad():
        image_features = model.encode_image(image)
        text_features = model.encode_text(text)

        # Normalize features
        image_features /= image_features.norm(dim=-1, keepdim=True)
        text_features /= text_features.norm(dim=-1, keepdim=True)

        # Calculate similarity
        similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)

    scores = similarity[0].cpu().numpy()

    # Calculate centered score: average of first two (centered) minus average of last three (bad)
    centered_score = float((scores[0] + scores[1]) / 2)
    bad_score = float((scores[2] + scores[3] + scores[4]) / 3)

    confidence = centered_score - bad_score

    return {
        'centered_score': centered_score,
        'bad_score': bad_score,
        'confidence': confidence,
        'scores': {
            'centered': float(scores[0]),
            'complete': float(scores[1]),
            'empty': float(scores[2]),
            'edge': float(scores[3]),
            'cutoff': float(scores[4])
        }
    }


def validate_sprite_layout(layout, model, preprocess, device):
    """Validate a sprite layout using CLIP."""
    if 'best_layout' not in layout:
        return {
            'validated': False,
            'reason': 'no_layout_detected'
        }

    bl = layout['best_layout']
    img_path = layout['file']

    # Extract sample frames
    samples = extract_sample_frames(
        img_path,
        bl['sprite_w'],
        bl['sprite_h'],
        bl['cols'],
        bl['rows'],
        num_samples=4
    )

    if not samples:
        return {
            'validated': False,
            'reason': 'no_frames_extracted'
        }

    # Pass detected dimensions to CLIP for context
    sprite_dims = {
        'sprite_w': bl['sprite_w'],
        'sprite_h': bl['sprite_h']
    }

    # Check each sample frame
    frame_results = []
    for sample in samples:
        result = check_subject_centered(
            sample['image'],
            model,
            preprocess,
            device,
            sprite_dims=sprite_dims  # Pass detected dimensions
        )
        result['frame_idx'] = sample['frame_idx']
        frame_results.append(result)

    # Calculate overall validation
    avg_confidence = sum(r['confidence'] for r in frame_results) / len(frame_results)

    # Validation threshold
    VALIDATION_THRESHOLD = 0.1  # Adjust based on testing
    validated = avg_confidence > VALIDATION_THRESHOLD

    return {
        'validated': validated,
        'confidence': float(avg_confidence),
        'frame_results': frame_results,
        'samples_checked': len(frame_results)
    }


def main():
    print("="*70)
    print("SPRITE LAYOUT VALIDATION WITH CLIP")
    print("="*70)

    # Load CLIP model
    print("\n📦 Loading CLIP model...")
    model, preprocess, device = load_clip_model()
    print(f"   Device: {device}")

    # Load sprite layouts
    print("\n📥 Loading sprite layouts...")
    with open('corpus/sprite_layouts.json') as f:
        layouts = json.load(f)
    print(f"   Loaded {len(layouts)} layouts")

    # Process layouts
    print("\n🔍 Validating layouts with CLIP...")

    results = []
    validated_count = 0

    for i, layout in enumerate(layouts):
        if (i + 1) % 10 == 0:
            print(f"   Progress: {i+1}/{len(layouts)}")

        # Only validate if we have a best_layout
        if 'best_layout' not in layout:
            continue

        validation = validate_sprite_layout(layout, model, preprocess, device)

        result = {
            'id': layout['id'],
            'title': layout['title'],
            'detected_layout': layout['best_layout'],  # What we detected
            'clip_validation': validation,  # What CLIP confirmed
            'final_confidence': 'validated' if validation['validated'] else 'needs_review',
            'metadata': {
                'detection_method': layout['best_layout']['method'],
                'detection_confidence': layout['confidence'],
                'perfect_fit': layout['best_layout']['perfect_fit']
            }
        }

        results.append(result)

        if validation['validated']:
            validated_count += 1

    # Save results
    output_file = 'corpus/validated_layouts.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    # Print summary
    print("\n" + "="*70)
    print("VALIDATION RESULTS")
    print("="*70)

    total_checked = len(results)
    validation_rate = (validated_count / total_checked * 100) if total_checked > 0 else 0

    print(f"\n📊 Statistics:")
    print(f"   Total layouts checked: {total_checked}")
    print(f"   ✓ Validated (subject centered): {validated_count}")
    print(f"   ✗ Failed validation: {total_checked - validated_count}")
    print(f"   Validation rate: {validation_rate:.1f}%")

    # Show some examples
    print(f"\n✅ Validated Examples:")
    validated_examples = [r for r in results if r['clip_validation']['validated']][:5]
    for r in validated_examples:
        print(f"   • {r['title']}")
        print(f"     Detected: {r['detected_layout']['sprite_w']}x{r['detected_layout']['sprite_h']} ({r['detected_layout']['method']})")
        print(f"     CLIP confidence: {r['clip_validation']['confidence']:.3f}")
        print(f"     Grid: {r['detected_layout']['cols']}x{r['detected_layout']['rows']} = {r['detected_layout']['total_frames']} frames")

    print(f"\n❌ Failed Validation Examples:")
    failed_examples = [r for r in results if not r['clip_validation']['validated']][:5]
    for r in failed_examples:
        print(f"   • {r['title']}")
        print(f"     Detected: {r['detected_layout']['sprite_w']}x{r['detected_layout']['sprite_h']} ({r['detected_layout']['method']})")
        print(f"     CLIP confidence: {r['clip_validation']['confidence']:.3f}")
        print(f"     → Detection likely incorrect, needs manual review")

    print(f"\n💾 Results saved to: {output_file}")
    print("="*70)


if __name__ == '__main__':
    main()
