.PHONY: help serve detect-directions detect-grid group-sprites install-tools install-ml test-tools benchmark clean clean-all

# Default target
help:
	@echo "Sprite Sheet Library - Development Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  serve              Start local development server (http://localhost:8000)"
	@echo "  detect-directions  Detect sprite animation directions"
	@echo "                     Usage: make detect-directions IMAGE=sprite.png ARGS='--ml'"
	@echo "  detect-grid        Auto-detect frame dimensions"
	@echo "                     Usage: make detect-grid IMAGE=sprite.png"
	@echo "  group-sprites      Group similar sprites by visual similarity"
	@echo "                     Usage: make group-sprites IMAGE=atlas.png"
	@echo "  install-tools      Create venv and install required Python dependencies"
	@echo "  install-ml         Install optional ML libraries (OpenCV, CLIP)"
	@echo "  test-tools         Test all tools on sample sprite"
	@echo "  benchmark          Run accuracy benchmark against ground truth corpus"
	@echo "  clean              Remove temporary files"
	@echo "  clean-all          Remove temporary files and virtual environment"
	@echo "  help               Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make serve"
	@echo "  make install-tools"
	@echo "  make detect-directions IMAGE=Green-Cap-Character.png ARGS='-w 16 -H 18 -f 3 -r 4 --ml'"
	@echo "  make detect-grid IMAGE=sprite.png"
	@echo "  make group-sprites IMAGE=atlas.png ARGS='-w 32 -h 32'"
	@echo "  make test-tools"

# Start development server
serve:
	@echo "Starting development server on http://localhost:8000"
	@echo "Press Ctrl+C to stop"
	@python3 server.py

# Detect sprite sheet animation directions
detect-directions:
	@if [ -z "$(IMAGE)" ]; then \
		echo "ERROR: IMAGE parameter required"; \
		echo "Usage: make detect-directions IMAGE=sprite.png"; \
		exit 1; \
	fi
	@if [ -d "tools/venv" ]; then \
		tools/venv/bin/python3 tools/detect_sprite_directions.py $(IMAGE) $(ARGS); \
	else \
		echo "ERROR: Virtual environment not found. Run 'make install-tools' first."; \
		exit 1; \
	fi

# Auto-detect frame grid dimensions
detect-grid:
	@if [ -z "$(IMAGE)" ]; then \
		echo "ERROR: IMAGE parameter required"; \
		echo "Usage: make detect-grid IMAGE=sprite.png"; \
		exit 1; \
	fi
	@if [ -d "tools/venv" ]; then \
		tools/venv/bin/python3 tools/detect_grid.py $(IMAGE) $(ARGS); \
	else \
		echo "ERROR: Virtual environment not found. Run 'make install-tools' first."; \
		exit 1; \
	fi

# Group sprites by similarity
group-sprites:
	@if [ -z "$(IMAGE)" ]; then \
		echo "ERROR: IMAGE parameter required"; \
		echo "Usage: make group-sprites IMAGE=atlas.png"; \
		exit 1; \
	fi
	@if [ -d "tools/venv" ]; then \
		tools/venv/bin/python3 tools/group_sprites.py $(IMAGE) $(ARGS); \
	else \
		echo "ERROR: Virtual environment not found. Run 'make install-tools' first."; \
		exit 1; \
	fi

# Install required Python tools dependencies
install-tools:
	@echo "Creating virtual environment..."
	@cd tools && python3 -m venv venv
	@echo "Upgrading pip..."
	@cd tools && ./venv/bin/pip install --quiet --upgrade pip
	@echo "Installing required Python dependencies..."
	@cd tools && ./venv/bin/pip install --quiet pillow numpy
	@echo "Done! Basic tools are ready."
	@echo "Virtual environment created at: tools/venv"
	@echo "For ML features, run: make install-ml"

# Install optional ML libraries
install-ml:
	@if [ ! -d "tools/venv" ]; then \
		echo "ERROR: Run 'make install-tools' first to create virtual environment"; \
		exit 1; \
	fi
	@echo "Installing ML libraries (this may take a while)..."
	@echo "  Installing OpenCV..."
	@cd tools && ./venv/bin/pip install opencv-python
	@echo "  Installing PyTorch (CPU-only)..."
	@cd tools && ./venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
	@echo "  Installing Transformers..."
	@cd tools && ./venv/bin/pip install transformers
	@echo "Done! ML features enabled."
	@echo "Note: CLIP model (~500MB) will download on first use."

# Test all tools on sample sprite
test-tools:
	@if [ ! -d "tools/venv" ]; then \
		echo "ERROR: Virtual environment not found. Run 'make install-tools' first."; \
		exit 1; \
	fi
	@echo "Testing sprite sheet tools..."
	@echo ""
	@echo "=== Testing Grid Detection ==="
	@tools/venv/bin/python3 tools/detect_grid.py Green-Cap-Character-16x18.png
	@echo ""
	@echo "=== Testing Direction Detection ==="
	@tools/venv/bin/python3 tools/detect_sprite_directions.py Green-Cap-Character-16x18.png -w 16 -H 18 -f 3 -r 4
	@echo ""
	@echo "=== Testing Direction Detection with ML ==="
	@tools/venv/bin/python3 tools/detect_sprite_directions.py Green-Cap-Character-16x18.png -w 16 -H 18 -f 3 -r 4 --ml
	@echo ""
	@echo "All tests complete!"

# Run accuracy benchmark against corpus
benchmark:
	@if [ ! -d "tools/venv" ]; then \
		echo "ERROR: Virtual environment not found. Run 'make install-tools' first."; \
		exit 1; \
	fi
	@tools/venv/bin/python3 tools/benchmark.py --verbose

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@echo "Done."

# Clean everything including virtual environment
clean-all: clean
	@echo "Removing virtual environment..."
	@rm -rf tools/venv
	@echo "Done. Run 'make install-tools' to reinstall."
