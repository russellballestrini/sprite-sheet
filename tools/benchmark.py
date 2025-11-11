#!/usr/bin/env python3
"""
Sprite Direction Detection Benchmark Tool

Tests detection algorithms against a ground truth corpus to measure accuracy.

Usage:
    python3 benchmark.py                    # Run full benchmark
    python3 benchmark.py --method opencv    # Test specific method
    python3 benchmark.py --verbose          # Show detailed results
"""

import argparse
import json
import sys
from pathlib import Path
from detect_sprite_directions import SpriteDirectionDetector, HAS_OPENCV, HAS_CLIP

def load_corpus():
    """Load ground truth corpus."""
    corpus_path = Path(__file__).parent / 'corpus.json'
    with open(corpus_path) as f:
        return json.load(f)

def calculate_accuracy(predicted, ground_truth):
    """Calculate accuracy metrics."""
    correct = 0
    total = 0
    errors = []

    for direction in ['down', 'up', 'left', 'right']:
        if direction in ground_truth:
            total += 1
            if predicted.get(direction) == ground_truth[direction]:
                correct += 1
            else:
                errors.append({
                    'direction': direction,
                    'predicted': predicted.get(direction),
                    'expected': ground_truth[direction]
                })

    accuracy = (correct / total * 100) if total > 0 else 0
    return accuracy, correct, total, errors

def test_sprite(sprite_data, method='all', verbose=False):
    """Test detection on a single sprite."""
    file_path = sprite_data['file']

    # Check if file exists, if not try to download
    if not Path(file_path).exists():
        print(f"  Downloading {sprite_data['name']}...")
        import urllib.request
        try:
            urllib.request.urlretrieve(sprite_data['url'], file_path)
        except Exception as e:
            print(f"  ✗ Failed to download: {e}")
            return None

    detector = SpriteDirectionDetector(
        file_path,
        sprite_data['frame_width'],
        sprite_data['frame_height'],
        sprite_data['frames_per_row'],
        sprite_data['rows']
    )

    ground_truth = sprite_data['ground_truth']
    results = {}

    # New API: detect_all_directions always runs ALL methods
    try:
        all_method_results, analyses, best_method = detector.detect_all_directions()

        # Extract results for each method
        for method_name, method_result in all_method_results.items():
            # Skip methods we're not testing
            if method != 'all' and method != method_name:
                continue

            dirs = method_result['directions']
            conf = method_result['confidence']
            accuracy, correct, total, errors = calculate_accuracy(dirs, ground_truth)

            results[method_name] = {
                'confidence': conf,
                'accuracy': accuracy,
                'correct': correct,
                'total': total,
                'directions': dirs,
                'errors': errors
            }

    except Exception as e:
        # If something fails, return error for all requested methods
        error_msg = str(e)
        if method == 'all':
            results = {
                'traditional': {'error': error_msg},
                'opencv': {'error': error_msg} if HAS_OPENCV else {'error': 'OpenCV not available'},
                'clip': {'error': error_msg} if HAS_CLIP else {'error': 'CLIP not available'}
            }
        else:
            results[method] = {'error': error_msg}

    return results

def main():
    parser = argparse.ArgumentParser(
        description='Benchmark sprite direction detection algorithms',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--method',
        choices=['all', 'traditional', 'opencv', 'clip'],
        default='all',
        help='Which detection method to test'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed results'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )

    args = parser.parse_args()

    # Load corpus
    corpus = load_corpus()

    if not args.json:
        print(f"\n📊 Sprite Direction Detection Benchmark")
        print("=" * 60)
        print(f"Corpus: {corpus['description']}")
        print(f"Sprites: {len(corpus['sprites'])}")
        print(f"Methods: {args.method}")
        print()

    all_results = []

    for sprite in corpus['sprites']:
        if not args.json:
            print(f"Testing: {sprite['name']} ({sprite['frame_width']}x{sprite['frame_height']})")
            print("-" * 60)

        results = test_sprite(sprite, args.method, args.verbose)

        if results:
            sprite_summary = {
                'sprite': sprite['name'],
                'size': f"{sprite['frame_width']}x{sprite['frame_height']}",
                'methods': results
            }
            all_results.append(sprite_summary)

            if not args.json:
                for method_name, method_results in results.items():
                    if 'error' in method_results:
                        print(f"  {method_name:12s}: Error - {method_results['error']}")
                    else:
                        acc = method_results['accuracy']
                        conf = method_results['confidence']
                        correct = method_results['correct']
                        total = method_results['total']

                        status = "✓" if acc == 100 else "✗"
                        print(f"  {method_name:12s}: {acc:5.1f}% accurate ({correct}/{total}) | conf: {conf:.2f} {status}")

                        if args.verbose and method_results.get('errors'):
                            for err in method_results['errors']:
                                print(f"    ✗ {err['direction']:>5s}: predicted Row {err['predicted']}, expected Row {err['expected']}")

                print()

    # Summary
    if not args.json:
        print("=" * 60)
        print("Summary:")
        print()

        method_accuracies = {}
        for result in all_results:
            for method_name, method_results in result['methods'].items():
                if 'accuracy' in method_results:
                    if method_name not in method_accuracies:
                        method_accuracies[method_name] = []
                    method_accuracies[method_name].append(method_results['accuracy'])

        for method_name, accuracies in method_accuracies.items():
            avg_acc = sum(accuracies) / len(accuracies) if accuracies else 0
            print(f"  {method_name:12s}: {avg_acc:.1f}% average accuracy")

        print()
        print("Recommendation: Add more sprites to corpus for better benchmarking!")
        print("Edit tools/corpus.json to add ground truth data.")
    else:
        print(json.dumps({
            'corpus': corpus['description'],
            'results': all_results
        }, indent=2))

if __name__ == '__main__':
    main()
