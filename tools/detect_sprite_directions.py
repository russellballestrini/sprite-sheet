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

# Optional: OpenCV for advanced ML-based detection
try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

# Optional: CLIP model for semantic understanding
try:
    from transformers import CLIPProcessor, CLIPModel
    import torch
    HAS_CLIP = True
except ImportError:
    HAS_CLIP = False


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

    def detect_facing_direction(self, frame):
        """
        Detect the facing direction by analyzing the top vs bottom density.
        For top-down sprites:
        - Down-facing: More detail/pixels at top (seeing head/shoulders)
        - Up-facing: More detail/pixels at bottom (seeing back of head)
        - Left/Right: Side profiles
        """
        if len(frame.shape) == 3:
            gray = np.mean(frame[:, :, :3], axis=2)
        else:
            gray = frame

        height = gray.shape[0]

        # Split into thirds
        top_third = gray[:height//3, :]
        middle_third = gray[height//3:2*height//3, :]
        bottom_third = gray[2*height//3:, :]

        # Calculate density (non-background pixels) in each section
        # Higher values mean more sprite content
        top_density = np.sum(top_third > top_third.mean())
        middle_density = np.sum(middle_third > middle_third.mean())
        bottom_density = np.sum(bottom_third > bottom_third.mean())

        # For down-facing sprites, top third is usually densest (head visible)
        # For up-facing sprites, pattern is more uniform or bottom-heavy

        # Return ratio: positive = top-heavy (likely down), negative = bottom-heavy (likely up)
        total = top_density + middle_density + bottom_density
        if total > 0:
            return (top_density - bottom_density) / total
        return 0

    def calculate_confidence(self, analyses):
        """
        Calculate confidence score for the detection.
        Returns 0.0-1.0 where 1.0 is very confident.
        """
        # Check how different the scores are
        facing_scores = [a['facing_score'] for a in analyses]
        asymmetry_scores = [abs(a['horizontal_asymmetry']) for a in analyses]

        # High confidence if there's clear separation between scores
        facing_range = max(facing_scores) - min(facing_scores)
        asymmetry_range = max(asymmetry_scores) - min(asymmetry_scores)

        # Normalize to 0-1 range (empirical thresholds)
        facing_confidence = min(1.0, facing_range / 0.3)
        asymmetry_confidence = min(1.0, asymmetry_range / 0.1)

        # Combined confidence
        return (facing_confidence + asymmetry_confidence) / 2

    def detect_with_optical_flow(self):
        """
        Use optical flow to detect movement patterns across animation frames.
        This is CPU-friendly and works well with temporal consistency.
        """
        if not HAS_OPENCV:
            return None, None

        analyses = []

        for i in range(self.num_rows):
            frames = self.extract_row(i)
            if len(frames) < 2:
                continue

            # Calculate optical flow between consecutive frames
            flow_vectors = []

            for j in range(len(frames) - 1):
                frame1 = frames[j]
                frame2 = frames[j + 1]

                # Convert to grayscale
                if len(frame1.shape) == 3:
                    gray1 = cv2.cvtColor(frame1.astype(np.uint8), cv2.COLOR_RGB2GRAY)
                    gray2 = cv2.cvtColor(frame2.astype(np.uint8), cv2.COLOR_RGB2GRAY)
                else:
                    gray1 = frame1.astype(np.uint8)
                    gray2 = frame2.astype(np.uint8)

                # Calculate dense optical flow
                flow = cv2.calcOpticalFlowFarneback(
                    gray1, gray2,
                    None,
                    pyr_scale=0.5,
                    levels=3,
                    winsize=5,
                    iterations=3,
                    poly_n=5,
                    poly_sigma=1.1,
                    flags=0
                )

                # Average flow vector
                avg_flow_x = np.mean(flow[..., 0])
                avg_flow_y = np.mean(flow[..., 1])
                flow_vectors.append((avg_flow_x, avg_flow_y))

            # Analyze overall movement pattern
            if flow_vectors:
                avg_x = np.mean([f[0] for f in flow_vectors])
                avg_y = np.mean([f[1] for f in flow_vectors])

                # Calculate dominant direction
                horizontal_motion = abs(avg_x)
                vertical_motion = abs(avg_y)

                analysis = {
                    'row': i,
                    'flow_x': avg_x,
                    'flow_y': avg_y,
                    'horizontal_motion': horizontal_motion,
                    'vertical_motion': vertical_motion,
                    'total_motion': np.sqrt(avg_x**2 + avg_y**2)
                }
                analyses.append(analysis)

        if not analyses:
            return None, None

        # Determine directions based on flow patterns
        directions = {}

        # For character sprites, look at the visual facing, not the animation motion
        # Use feature detection on static poses instead
        return self.detect_with_opencv_features(), None

    def detect_with_opencv_features(self):
        """
        Use feature detection and clustering for direction detection.
        CPU-friendly and works well on small sprites.
        """
        if not HAS_OPENCV:
            return None, None

        analyses = []

        for i in range(self.num_rows):
            frames = self.extract_row(i)
            if not frames:
                continue

            # Use first frame for static analysis
            frame = frames[0]

            # Upscale small sprites for better feature detection
            if frame.shape[0] < 32 or frame.shape[1] < 32:
                scale_factor = max(2, 32 // min(frame.shape[0], frame.shape[1]))
                frame = cv2.resize(
                    frame.astype(np.uint8),
                    None,
                    fx=scale_factor,
                    fy=scale_factor,
                    interpolation=cv2.INTER_CUBIC
                )

            # Convert to grayscale
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame.astype(np.uint8), cv2.COLOR_RGB2GRAY)
            else:
                gray = frame.astype(np.uint8)

            # Feature extraction using multiple methods
            # 1. HOG (Histogram of Oriented Gradients)
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

            magnitude = np.sqrt(sobelx**2 + sobely**2)
            angle = np.arctan2(sobely, sobelx)

            # 2. Spatial moments for shape analysis
            moments = cv2.moments(gray)

            # 3. Top vs bottom pixel density (works for top-down sprites)
            height = gray.shape[0]
            top_half = gray[:height//2, :]
            bottom_half = gray[height//2:, :]

            top_density = np.sum(top_half > np.mean(top_half))
            bottom_density = np.sum(bottom_half > np.mean(bottom_half))

            # 4. Left vs right asymmetry
            width = gray.shape[1]
            left_half = gray[:, :width//2]
            right_half = gray[:, width//2:]

            left_density = np.sum(left_half > np.mean(left_half))
            right_density = np.sum(right_half > np.mean(right_half))

            # 5. Edge detection for structural analysis
            edges = cv2.Canny(gray, 50, 150)
            edge_top = np.sum(edges[:height//3, :])
            edge_middle = np.sum(edges[height//3:2*height//3, :])
            edge_bottom = np.sum(edges[2*height//3:, :])

            analysis = {
                'row': i,
                'top_density': top_density,
                'bottom_density': bottom_density,
                'left_density': left_density,
                'right_density': right_density,
                'edge_top': edge_top,
                'edge_middle': edge_middle,
                'edge_bottom': edge_bottom,
                'vertical_score': (top_density - bottom_density) / (top_density + bottom_density + 1e-6),
                'horizontal_score': (right_density - left_density) / (right_density + left_density + 1e-6),
                'top_edge_ratio': edge_top / (edge_top + edge_middle + edge_bottom + 1e-6)
            }
            analyses.append(analysis)

        if not analyses:
            return None, None

        # Determine directions using ensemble of features
        directions = {}

        # Down-facing: usually top-heavy (seeing head/shoulders)
        down_candidates = sorted(analyses, key=lambda x: x['vertical_score'], reverse=True)
        directions['down'] = down_candidates[0]['row']

        # Up-facing: usually bottom-heavy or uniform
        up_candidates = sorted(analyses, key=lambda x: x['vertical_score'])
        directions['up'] = up_candidates[0]['row']

        # Left/right based on horizontal asymmetry
        remaining = [a for a in analyses if a['row'] not in [directions['down'], directions['up']]]

        if len(remaining) >= 2:
            remaining_sorted = sorted(remaining, key=lambda x: x['horizontal_score'])
            directions['left'] = remaining_sorted[0]['row']
            directions['right'] = remaining_sorted[1]['row']
        elif len(remaining) == 1:
            if remaining[0]['horizontal_score'] > 0:
                directions['right'] = remaining[0]['row']
            else:
                directions['left'] = remaining[0]['row']

        # Calculate confidence based on feature separation
        vertical_scores = [a['vertical_score'] for a in analyses]
        horizontal_scores = [abs(a['horizontal_score']) for a in remaining] if remaining else [0]

        vertical_separation = max(vertical_scores) - min(vertical_scores)
        horizontal_separation = max(horizontal_scores) - min(horizontal_scores) if horizontal_scores else 0

        # Confidence is based on how well separated the features are
        confidence = min(1.0, (vertical_separation + horizontal_separation) / 1.0)

        return directions, confidence

    def detect_with_opencv(self):
        """Use OpenCV's advanced features for better detection."""
        # Delegate to the improved feature-based detection
        return self.detect_with_opencv_features()

    def detect_with_clip(self, analyze_all_frames=False):
        """
        Use CLIP model to semantically understand sprite directions.
        Analyzes frames by asking multiple detailed questions about visual features.

        Args:
            analyze_all_frames: If True, analyze all animation frames and average results.
                              If False (default), only analyze first frame (faster, often better).
        """
        if not HAS_CLIP:
            return None, None

        print("  Loading CLIP model (this may take a moment)...")
        model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

        # Multi-question approach: ask separate questions about visual features
        # This wastes cycles but builds better understanding

        # Question 1: Front vs Back (most critical distinction)
        front_back_prompts = [
            "pixel art character viewed from the front showing face",
            "pixel art character viewed from behind showing back"
        ]

        # Question 2: Left vs Right profile (critical for side views)
        left_right_prompts = [
            "pixel art character walking left with body facing left",
            "pixel art character walking right with body facing right"
        ]

        # Question 3: Vertical orientation - What angle are we viewing from?
        vertical_prompts = [
            "top-down RPG sprite showing character from above",
            "game character sprite showing front and face",
            "game character sprite showing back and shoulders",
            "side view game character sprite"
        ]

        # Question 4: Specific body part visibility
        body_parts_prompts = [
            "seeing the front of a face",
            "seeing the top of a head from above",
            "seeing a person's back",
            "seeing a side profile"
        ]

        # Question 5: Movement direction (for walking sprites)
        movement_prompts = [
            "character moving downward on screen",
            "character moving upward on screen",
            "character moving to the left",
            "character moving to the right"
        ]

        row_analyses = []

        # Analyze each row with multiple question sets
        for i in range(self.num_rows):
            frames = self.extract_row(i)
            if not frames:
                continue

            # Analyze ALL frames in the row and average results for robustness
            row_analysis = {'row': i}

            # Initialize accumulators
            accumulators = {
                'is_front': 0, 'is_back': 0,
                'is_left_profile': 0, 'is_right_profile': 0,
                'is_top_down_view': 0, 'is_face_on_view': 0, 'is_back_view': 0, 'is_side_view': 0,
                'shows_face': 0, 'shows_top_of_head': 0, 'shows_back': 0, 'shows_profile': 0,
                'moving_down': 0, 'moving_up': 0, 'moving_left': 0, 'moving_right': 0
            }

            # Decide which frames to analyze
            frames_to_analyze = frames if analyze_all_frames else [frames[0]]

            # Ask questions for selected frame(s)
            for frame in frames_to_analyze:
                frame_pil = Image.fromarray(frame.astype(np.uint8))

                # Upscale tiny sprites
                if frame_pil.size[0] < 64 or frame_pil.size[1] < 64:
                    scale = max(2, 64 // min(frame_pil.size))
                    new_size = (frame_pil.size[0] * scale, frame_pil.size[1] * scale)
                    frame_pil = frame_pil.resize(new_size, Image.NEAREST)

                # Ask Question 1: Front or Back?
                inputs = processor(text=front_back_prompts, images=frame_pil, return_tensors="pt", padding=True)
                with torch.no_grad():
                    outputs = model(**inputs)
                    probs = outputs.logits_per_image.softmax(dim=1)[0]
                    accumulators['is_front'] += probs[0].item()
                    accumulators['is_back'] += probs[1].item()

                # Ask Question 2: Left or Right profile?
                inputs = processor(text=left_right_prompts, images=frame_pil, return_tensors="pt", padding=True)
                with torch.no_grad():
                    outputs = model(**inputs)
                    probs = outputs.logits_per_image.softmax(dim=1)[0]
                    accumulators['is_left_profile'] += probs[0].item()
                    accumulators['is_right_profile'] += probs[1].item()

                # Ask Question 3: Vertical orientation
                inputs = processor(text=vertical_prompts, images=frame_pil, return_tensors="pt", padding=True)
                with torch.no_grad():
                    outputs = model(**inputs)
                    probs = outputs.logits_per_image.softmax(dim=1)[0]
                    accumulators['is_top_down_view'] += probs[0].item()
                    accumulators['is_face_on_view'] += probs[1].item()
                    accumulators['is_back_view'] += probs[2].item()
                    accumulators['is_side_view'] += probs[3].item()

                # Ask Question 4: Body parts
                inputs = processor(text=body_parts_prompts, images=frame_pil, return_tensors="pt", padding=True)
                with torch.no_grad():
                    outputs = model(**inputs)
                    probs = outputs.logits_per_image.softmax(dim=1)[0]
                    accumulators['shows_face'] += probs[0].item()
                    accumulators['shows_top_of_head'] += probs[1].item()
                    accumulators['shows_back'] += probs[2].item()
                    accumulators['shows_profile'] += probs[3].item()

                # Ask Question 5: Movement direction
                inputs = processor(text=movement_prompts, images=frame_pil, return_tensors="pt", padding=True)
                with torch.no_grad():
                    outputs = model(**inputs)
                    probs = outputs.logits_per_image.softmax(dim=1)[0]
                    accumulators['moving_down'] += probs[0].item()
                    accumulators['moving_up'] += probs[1].item()
                    accumulators['moving_left'] += probs[2].item()
                    accumulators['moving_right'] += probs[3].item()

            # Average across analyzed frames
            num_analyzed = len(frames_to_analyze)
            for key in accumulators:
                row_analysis[key] = accumulators[key] / num_analyzed

            row_analyses.append(row_analysis)

        # Synthesize answers into direction detection
        directions = {}

        # Down: front view + face visible + moving down
        # Weight front/face indicators higher for down
        down_scores = [(a['row'],
                       a['is_front'] * 2.0 +
                       a['shows_face'] * 2.0 +
                       a['is_face_on_view'] * 1.5 +
                       a['shows_top_of_head'] * 1.0 +
                       a['is_top_down_view'] * 1.0 +
                       a['moving_down'] * 1.0)
                       for a in row_analyses]

        # Up: back view + shows back + moving up
        # Weight back indicators higher for up
        up_scores = [(a['row'],
                     a['is_back'] * 2.0 +
                     a['shows_back'] * 2.0 +
                     a['is_back_view'] * 1.5 +
                     a['moving_up'] * 1.0)
                     for a in row_analyses]

        # Left: left profile + side view + side profile + moving left
        left_scores = [(a['row'],
                       a['is_left_profile'] * 3.0 +
                       a['is_side_view'] * 1.0 +
                       a['shows_profile'] * 1.0 +
                       a['moving_left'] * 1.5)
                       for a in row_analyses]

        # Right: right profile + side view + side profile + moving right
        right_scores = [(a['row'],
                        a['is_right_profile'] * 3.0 +
                        a['is_side_view'] * 1.0 +
                        a['shows_profile'] * 1.0 +
                        a['moving_right'] * 1.5)
                        for a in row_analyses]

        # Assign rows based on highest composite scores
        used_rows = set()

        # Down: highest down score
        down_candidates = sorted(down_scores, key=lambda x: x[1], reverse=True)
        for row, score in down_candidates:
            if row not in used_rows:
                directions['down'] = row
                used_rows.add(row)
                break

        # Up: highest up score (excluding used rows)
        up_candidates = sorted([s for s in up_scores if s[0] not in used_rows], key=lambda x: x[1], reverse=True)
        if up_candidates:
            directions['up'] = up_candidates[0][0]
            used_rows.add(up_candidates[0][0])

        # Left: highest left score (excluding used rows)
        left_candidates = sorted([s for s in left_scores if s[0] not in used_rows], key=lambda x: x[1], reverse=True)
        if left_candidates:
            directions['left'] = left_candidates[0][0]
            used_rows.add(left_candidates[0][0])

        # Right: highest right score (excluding used rows)
        right_candidates = sorted([s for s in right_scores if s[0] not in used_rows], key=lambda x: x[1], reverse=True)
        if right_candidates:
            directions['right'] = right_candidates[0][0]
            used_rows.add(right_candidates[0][0])

        # Calculate confidence based on score separation
        all_composite_scores = [s[1] for s in down_scores + up_scores + left_scores + right_scores]
        if all_composite_scores:
            max_score = max(all_composite_scores)
            avg_score = np.mean(all_composite_scores)
            confidence = float((max_score - avg_score) / (max_score + 1e-6))
        else:
            confidence = 0.0

        return directions, confidence

    def detect_all_directions(self, use_ml=False, clip_all_frames=False):
        """Analyze all rows and determine directions using ALL available methods.

        Always runs traditional CV, OpenCV (if available), and CLIP (if available).
        Returns results from all methods so user can choose the best one.

        Args:
            use_ml: Ignored - always runs all methods now
            clip_all_frames: If using CLIP, analyze all animation frames (slower)

        Returns:
            Dictionary containing results from all methods
        """
        analyses = []

        for i in range(self.num_rows):
            analysis = self.analyze_row(i)

            # Add facing direction analysis (using first frame for static pose)
            frames = self.extract_row(i)
            if frames:
                analysis['facing_score'] = self.detect_facing_direction(frames[0])
            else:
                analysis['facing_score'] = 0

            analyses.append(analysis)

        # Calculate confidence for traditional approach
        traditional_confidence = self.calculate_confidence(analyses)

        # Determine directions based on traditional analysis
        traditional_directions = {}

        # Strategy: Use facing_score combined with horizontal asymmetry
        # Down-facing sprites have positive facing_score (top-heavy detail)
        # Up-facing sprites have negative or low facing_score (bottom-heavy)

        # Sort by facing score to find down (highest score = most top-heavy)
        sorted_by_facing = sorted(analyses, key=lambda x: x['facing_score'], reverse=True)

        # The most top-heavy sprite is likely facing down
        traditional_directions['down'] = sorted_by_facing[0]['row']

        # The most bottom-heavy sprite is likely facing up
        traditional_directions['up'] = sorted_by_facing[-1]['row']

        # For left/right, use horizontal asymmetry from remaining rows
        remaining = [a for a in analyses if a['row'] not in [traditional_directions['down'], traditional_directions['up']]]

        if len(remaining) >= 2:
            # Right-facing has positive horizontal asymmetry (more pixels on right)
            right_row = max(remaining, key=lambda x: x['horizontal_asymmetry'])
            traditional_directions['right'] = right_row['row']

            # Left is the other one
            left_row = [a for a in remaining if a['row'] != traditional_directions['right']][0]
            traditional_directions['left'] = left_row['row']
        elif len(remaining) == 1:
            # Only one horizontal direction, guess based on asymmetry
            if remaining[0]['horizontal_asymmetry'] > 0:
                traditional_directions['right'] = remaining[0]['row']
            else:
                traditional_directions['left'] = remaining[0]['row']

        # Now run ALL available methods and collect results
        all_results = {
            'traditional': {
                'directions': traditional_directions,
                'confidence': traditional_confidence
            }
        }

        # Try OpenCV
        if HAS_OPENCV:
            try:
                opencv_directions, opencv_confidence = self.detect_with_opencv()
                if opencv_directions:
                    all_results['opencv'] = {
                        'directions': opencv_directions,
                        'confidence': opencv_confidence
                    }
            except Exception as e:
                print(f"  ⚠ OpenCV detection failed: {e}")

        # Try CLIP
        if HAS_CLIP:
            try:
                clip_directions, clip_confidence = self.detect_with_clip(analyze_all_frames=clip_all_frames)
                if clip_directions:
                    all_results['clip'] = {
                        'directions': clip_directions,
                        'confidence': clip_confidence
                    }
            except Exception as e:
                print(f"  ⚠ CLIP detection failed: {e}")

        # For backward compatibility, return the best performing method as the primary result
        best_method = 'traditional'
        best_confidence = traditional_confidence
        best_directions = traditional_directions

        for method_name, result in all_results.items():
            if result['confidence'] > best_confidence:
                best_method = method_name
                best_confidence = result['confidence']
                best_directions = result['directions']

        return all_results, analyses, best_method


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
    parser.add_argument('--ml', action='store_true', help='Use ML enhancement for low confidence detections')
    parser.add_argument('--clip-all-frames', action='store_true', help='Analyze all animation frames with CLIP (slower, may reduce accuracy)')

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

        all_results, analyses, best_method = detector.detect_all_directions(
            use_ml=args.ml,
            clip_all_frames=args.clip_all_frames
        )

        if args.json:
            import json
            output = {
                'all_results': all_results,
                'best_method': best_method,
                'analyses': analyses if args.verbose else None
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"\n🎮 Sprite Direction Detection Results for: {args.image}")
            print("=" * 60)
            print("\n⚠️  NOTE: Automated detection is experimental!")
            print("Verify results visually - sprite sheets vary greatly in style.")

            # Special warning for very small sprites
            if args.width < 24 or args.height < 24:
                print(f"\n⚠️  Small sprite ({args.width}x{args.height}) - results may be less reliable")
                print("Recommendation: Test in your game and adjust row mapping as needed")

            # Display results from ALL methods
            print(f"\n📊 Results from all methods:\n")
            for method_name, result in all_results.items():
                confidence = result['confidence']
                directions = result['directions']

                # Confidence indicator
                if confidence >= 0.90:
                    conf_str = "Very High"
                elif confidence >= 0.75:
                    conf_str = "High"
                elif confidence >= 0.50:
                    conf_str = "Medium"
                else:
                    conf_str = "Low"

                # Mark best method
                best_marker = " ⭐ BEST" if method_name == best_method else ""

                print(f"{method_name.upper()}: {confidence:.2f} ({conf_str}){best_marker}")
                for direction in ['down', 'left', 'right', 'up']:
                    if direction in directions:
                        print(f"  {direction:>6}: Row {directions[direction]}")
                print()

            if args.verbose:
                print(f"\nDetailed Analysis:")
                print("-" * 60)
                for analysis in analyses:
                    print(f"\nRow {analysis['row']}:")
                    print(f"  Facing Score:         {analysis['facing_score']:>8.3f} " +
                          f"({'top-heavy/down' if analysis['facing_score'] > 0.05 else 'bottom-heavy/up' if analysis['facing_score'] < -0.05 else 'neutral'})")
                    print(f"  Horizontal Asymmetry: {analysis['horizontal_asymmetry']:>8.3f} " +
                          f"({'right' if analysis['horizontal_asymmetry'] > 0 else 'left' if analysis['horizontal_asymmetry'] < 0 else 'centered'})")
                    print(f"  Vertical Motion:      {analysis['vertical_motion']:>8.3f} " +
                          f"(animation motion)")
                    print(f"  Motion Amount:        {analysis['motion_amount']:>8.3f}")

            # Show JavaScript config using the best method
            best_directions = all_results[best_method]['directions']
            print("\n" + "=" * 60)
            print(f"\n📋 JavaScript Config (using {best_method.upper()}):")
            print(f"""
const animations = {{
  down: {{ regionY: {best_directions.get('down', 0)} * frameHeight }},
  left: {{ regionY: {best_directions.get('left', 1)} * frameHeight }},
  right: {{ regionY: {best_directions.get('right', 2)} * frameHeight }},
  up: {{ regionY: {best_directions.get('up', 3)} * frameHeight }}
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
