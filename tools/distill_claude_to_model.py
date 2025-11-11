#!/usr/bin/env python3
"""
Model Distillation: Use Claude's vision understanding to create training data
for a small, specialized sprite direction detection model.

This script:
1. Uses Claude API to analyze sprite sheets
2. Collects Claude's labels and reasoning
3. Generates a training dataset
4. Fine-tunes a small vision model (MobileNetV3 or EfficientNet)

Usage:
    python3 distill_claude_to_model.py --collect-data sprites/*.png
    python3 distill_claude_to_model.py --train training_data.json
    python3 distill_claude_to_model.py --test model.pth sprite.png
"""

import argparse
import json
import base64
from pathlib import Path
from PIL import Image
import numpy as np

def extract_sprite_frames(image_path, frame_width, frame_height, rows):
    """Extract individual row images from sprite sheet."""
    img = Image.open(image_path)
    row_images = []

    for row in range(rows):
        y = row * frame_height
        # Extract just the first frame of each row for analysis
        row_crop = img.crop((0, y, frame_width, y + frame_height))
        row_images.append(row_crop)

    return row_images

def ask_claude_to_label_sprite(row_images, api_key):
    """
    Send sprite row images to Claude and ask for direction labels.

    This would use the Anthropic API to send images and get structured responses.
    For now, this is a placeholder showing the concept.
    """
    # NOTE: This requires the Anthropic API client
    # pip install anthropic

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    # Convert images to base64
    encoded_images = []
    for img in row_images:
        from io import BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_bytes = buffer.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        encoded_images.append(img_base64)

    # Create a message with all 4 row images
    content = [
        {
            "type": "text",
            "text": """I'm showing you 4 sprite animation frames from a character sprite sheet.
Each image is from a different row (Row 0, Row 1, Row 2, Row 3).

Please analyze each row and determine which direction the character is facing:
- DOWN (front view, face visible)
- UP (back view, back visible)
- LEFT (left profile)
- RIGHT (right profile)

Return your answer as JSON:
{
  "row_0": {"direction": "down", "confidence": 0.95, "reasoning": "Face clearly visible"},
  "row_1": {"direction": "left", "confidence": 0.90, "reasoning": "Left profile visible"},
  "row_2": {"direction": "right", "confidence": 0.90, "reasoning": "Right profile visible"},
  "row_3": {"direction": "up", "confidence": 0.85, "reasoning": "Back/shoulders visible"}
}"""
        }
    ]

    # Add each image
    for i, img_b64 in enumerate(encoded_images):
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": img_b64
            }
        })
        content.append({
            "type": "text",
            "text": f"Row {i}"
        })

    # Call Claude API
    message = client.messages.create(
        model="claude-sonnet-4-20250514",  # Use latest Claude with vision
        max_tokens=1024,
        messages=[{"role": "user", "content": content}]
    )

    # Parse response
    response_text = message.content[0].text

    # Extract JSON from response
    import re
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        labels = json.loads(json_match.group())
        return labels
    else:
        raise ValueError(f"Could not parse JSON from Claude's response: {response_text}")

def collect_training_data(sprite_paths, output_file, api_key):
    """
    Collect training data by asking Claude to label sprites.
    """
    training_data = []

    for sprite_path in sprite_paths:
        print(f"Processing {sprite_path}...")

        # For this demo, assume standard 4-direction sprite sheets
        # In practice, you'd detect dimensions first
        frame_width = 16  # This should be auto-detected
        frame_height = 18
        rows = 4

        try:
            # Extract row images
            row_images = extract_sprite_frames(sprite_path, frame_width, frame_height, rows)

            # Ask Claude to label them
            labels = ask_claude_to_label_sprite(row_images, api_key)

            # Save to training data
            training_example = {
                'sprite_path': str(sprite_path),
                'frame_width': frame_width,
                'frame_height': frame_height,
                'rows': rows,
                'labels': labels,
                'metadata': {
                    'labeled_by': 'claude-sonnet-4',
                    'confidence_scores': {
                        row: data['confidence']
                        for row, data in labels.items()
                    }
                }
            }
            training_data.append(training_example)

        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue

    # Save training data
    with open(output_file, 'w') as f:
        json.dump(training_data, f, indent=2)

    print(f"\n✓ Collected {len(training_data)} training examples")
    print(f"  Saved to {output_file}")

def train_small_model(training_data_file, output_model_file):
    """
    Train a small MobileNetV3 model using Claude's labels.
    """
    print("Training small model from Claude's labels...")

    # NOTE: This requires PyTorch
    # pip install torch torchvision

    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    import torchvision.models as models
    from torchvision import transforms

    # Load training data
    with open(training_data_file) as f:
        training_data = json.load(f)

    # Create custom dataset
    class SpriteDataset(Dataset):
        def __init__(self, training_data, transform=None):
            self.data = training_data
            self.transform = transform
            self.direction_to_idx = {'down': 0, 'up': 1, 'left': 2, 'right': 3}

        def __len__(self):
            return len(self.data) * 4  # 4 rows per sprite

        def __getitem__(self, idx):
            sprite_idx = idx // 4
            row_idx = idx % 4

            sprite_info = self.data[sprite_idx]

            # Load sprite image
            img = Image.open(sprite_info['sprite_path'])

            # Extract this row
            row = row_idx
            frame_height = sprite_info['frame_height']
            frame_width = sprite_info['frame_width']
            y = row * frame_height

            row_img = img.crop((0, y, frame_width, y + frame_height))

            # Get label for this row
            row_key = f"row_{row_idx}"
            direction = sprite_info['labels'][row_key]['direction']
            label = self.direction_to_idx[direction]

            # Apply transforms
            if self.transform:
                row_img = self.transform(row_img)

            return row_img, label

    # Define transforms
    transform = transforms.Compose([
        transforms.Resize((64, 64)),  # Resize to consistent size
        transforms.ToTensor(),
        transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
    ])

    # Create dataset and dataloader
    dataset = SpriteDataset(training_data, transform=transform)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)

    # Create small model (MobileNetV3-Small)
    model = models.mobilenet_v3_small(pretrained=True)

    # Modify classifier for 4-class output
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, 4)

    # Training setup
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    # Train for a few epochs
    num_epochs = 20

    print(f"Training on {len(dataset)} examples for {num_epochs} epochs...")

    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for inputs, labels in dataloader:
            inputs, labels = inputs.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()

            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

        accuracy = 100.0 * correct / total
        avg_loss = running_loss / len(dataloader)

        print(f"Epoch {epoch+1}/{num_epochs} - Loss: {avg_loss:.4f}, Accuracy: {accuracy:.2f}%")

    # Save model
    torch.save({
        'model_state_dict': model.state_dict(),
        'direction_map': {0: 'down', 1: 'up', 2: 'left', 3: 'right'}
    }, output_model_file)

    print(f"\n✓ Model saved to {output_model_file}")
    print(f"  Model size: ~5MB (MobileNetV3-Small)")
    print(f"  Final accuracy: {accuracy:.2f}%")

def test_model(model_file, sprite_path):
    """Test the trained model on a new sprite."""
    import torch
    import torchvision.models as models
    from torchvision import transforms

    # Load model
    checkpoint = torch.load(model_file)
    model = models.mobilenet_v3_small(pretrained=False)
    model.classifier[3] = torch.nn.Linear(model.classifier[3].in_features, 4)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()

    direction_map = checkpoint['direction_map']

    # Load and preprocess sprite
    transform = transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.ToTensor(),
        transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
    ])

    img = Image.open(sprite_path)

    # Assume 4 rows, detect each
    print(f"\nTesting {sprite_path}:\n")

    for row in range(4):
        # Extract row
        frame_height = 18  # This should be auto-detected
        y = row * frame_height
        row_img = img.crop((0, y, 16, y + frame_height))

        # Run inference
        input_tensor = transform(row_img).unsqueeze(0)

        with torch.no_grad():
            output = model(input_tensor)
            probabilities = torch.nn.functional.softmax(output[0], dim=0)
            predicted_idx = output.argmax(1).item()
            confidence = probabilities[predicted_idx].item()

        predicted_direction = direction_map[predicted_idx]

        print(f"  Row {row}: {predicted_direction.upper():>6s} (confidence: {confidence:.2f})")

def main():
    parser = argparse.ArgumentParser(
        description='Distill Claude vision model into small sprite detector'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Collect data command
    collect_parser = subparsers.add_parser('collect', help='Collect training data using Claude')
    collect_parser.add_argument('sprites', nargs='+', help='Sprite sheet files')
    collect_parser.add_argument('--output', default='training_data.json', help='Output file')
    collect_parser.add_argument('--api-key', required=True, help='Anthropic API key')

    # Train command
    train_parser = subparsers.add_parser('train', help='Train small model')
    train_parser.add_argument('training_data', help='Training data JSON file')
    train_parser.add_argument('--output', default='sprite_detector.pth', help='Output model file')

    # Test command
    test_parser = subparsers.add_parser('test', help='Test trained model')
    test_parser.add_argument('model', help='Trained model file')
    test_parser.add_argument('sprite', help='Sprite to test')

    args = parser.parse_args()

    if args.command == 'collect':
        collect_training_data(args.sprites, args.output, args.api_key)
    elif args.command == 'train':
        train_small_model(args.training_data, args.output)
    elif args.command == 'test':
        test_model(args.model, args.sprite)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
