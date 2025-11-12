.PHONY: help setup clean clean-all fetch fetch-all fetch-test split verify stats

# Configuration
PYTHON := python3
PIP := pip3
CORPUS_DIR := corpus
TARGET_COUNT := 3000
TRAIN_RATIO := 0.8

# Colors for output
COLOR_RESET := \033[0m
COLOR_BOLD := \033[1m
COLOR_GREEN := \033[32m
COLOR_YELLOW := \033[33m
COLOR_BLUE := \033[34m

help: ## Show this help message
	@echo "$(COLOR_BOLD)Sprite Sheet Corpus Management$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_BOLD)Available targets:$(COLOR_RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(COLOR_GREEN)%-20s$(COLOR_RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(COLOR_BOLD)Configuration:$(COLOR_RESET)"
	@echo "  CORPUS_DIR    = $(CORPUS_DIR)"
	@echo "  TARGET_COUNT  = $(TARGET_COUNT)"
	@echo "  TRAIN_RATIO   = $(TRAIN_RATIO)"
	@echo ""
	@echo "$(COLOR_BOLD)Quick start:$(COLOR_RESET)"
	@echo "  make setup      # Install dependencies"
	@echo "  make fetch-all  # Download entire dataset (~7,302 sprites)"
	@echo "  make split      # Create train/test splits"
	@echo "  make stats      # View corpus statistics"

setup: ## Install Python dependencies
	@echo "$(COLOR_BLUE)Installing dependencies...$(COLOR_RESET)"
	$(PIP) install --quiet -r requirements.txt
	@echo "$(COLOR_GREEN)✓ Dependencies installed$(COLOR_RESET)"

fetch-test: setup ## Fetch a small test set (10 sprites)
	@echo "$(COLOR_BLUE)Fetching test set (10 sprites)...$(COLOR_RESET)"
	$(PYTHON) fetch_sprites.py --target 10 --max-items 50 --source huggingface
	@$(MAKE) stats

fetch: setup ## Fetch sprites (default: 3000 target)
	@echo "$(COLOR_BLUE)Fetching $(TARGET_COUNT) sprites...$(COLOR_RESET)"
	$(PYTHON) fetch_sprites.py --target $(TARGET_COUNT) --corpus-dir $(CORPUS_DIR) --source huggingface
	@$(MAKE) stats

fetch-all: setup ## Fetch entire 2D art dataset (~7,302 sprites)
	@echo "$(COLOR_BLUE)Fetching entire dataset (7302 sprites)...$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)⚠ This may take a while and use significant disk space$(COLOR_RESET)"
	$(PYTHON) fetch_sprites.py --target 7302 --corpus-dir $(CORPUS_DIR) --source huggingface
	@$(MAKE) stats

fetch-resume: ## Resume interrupted download
	@echo "$(COLOR_BLUE)Resuming download...$(COLOR_RESET)"
	$(PYTHON) fetch_sprites.py --target $(TARGET_COUNT) --corpus-dir $(CORPUS_DIR) --source huggingface
	@$(MAKE) stats

split: ## Split corpus into train/test sets
	@echo "$(COLOR_BLUE)Creating train/test split (ratio: $(TRAIN_RATIO))...$(COLOR_RESET)"
	$(PYTHON) split_corpus.py --corpus-dir $(CORPUS_DIR) --train-ratio $(TRAIN_RATIO)
	@echo "$(COLOR_GREEN)✓ Train/test split complete$(COLOR_RESET)"
	@$(MAKE) stats

verify: ## Verify corpus integrity
	@echo "$(COLOR_BLUE)Verifying corpus...$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_BOLD)Raw sprites:$(COLOR_RESET)"
	@ls -1 $(CORPUS_DIR)/raw/ | wc -l || echo "0"
	@echo ""
	@echo "$(COLOR_BOLD)Metadata files:$(COLOR_RESET)"
	@ls -1 $(CORPUS_DIR)/metadata/ | wc -l || echo "0"
	@echo ""
	@echo "$(COLOR_BOLD)Training set:$(COLOR_RESET)"
	@if [ -d "$(CORPUS_DIR)/train" ]; then ls -1 $(CORPUS_DIR)/train/*.png $(CORPUS_DIR)/train/*.gif $(CORPUS_DIR)/train/*.jpg 2>/dev/null | wc -l || echo "0"; else echo "Not created yet"; fi
	@echo ""
	@echo "$(COLOR_BOLD)Test set:$(COLOR_RESET)"
	@if [ -d "$(CORPUS_DIR)/test" ]; then ls -1 $(CORPUS_DIR)/test/*.png $(CORPUS_DIR)/test/*.gif $(CORPUS_DIR)/test/*.jpg 2>/dev/null | wc -l || echo "0"; else echo "Not created yet"; fi
	@echo ""
	@echo "$(COLOR_BOLD)Disk usage:$(COLOR_RESET)"
	@du -sh $(CORPUS_DIR)/* 2>/dev/null || echo "Corpus not initialized"

stats: ## Show corpus statistics
	@echo ""
	@echo "$(COLOR_BOLD)═══════════════════════════════════════════════════$(COLOR_RESET)"
	@echo "$(COLOR_BOLD)  Sprite Sheet Corpus Statistics$(COLOR_RESET)"
	@echo "$(COLOR_BOLD)═══════════════════════════════════════════════════$(COLOR_RESET)"
	@echo ""
	@printf "$(COLOR_BOLD)%-25s$(COLOR_RESET) " "Raw sprites:"
	@ls -1 $(CORPUS_DIR)/raw/ 2>/dev/null | wc -l || echo "0"
	@printf "$(COLOR_BOLD)%-25s$(COLOR_RESET) " "Metadata files:"
	@ls -1 $(CORPUS_DIR)/metadata/ 2>/dev/null | wc -l || echo "0"
	@printf "$(COLOR_BOLD)%-25s$(COLOR_RESET) " "Training sprites:"
	@if [ -d "$(CORPUS_DIR)/train" ]; then find $(CORPUS_DIR)/train -type l 2>/dev/null | wc -l || echo "0"; else echo "Not split yet"; fi
	@printf "$(COLOR_BOLD)%-25s$(COLOR_RESET) " "Test sprites:"
	@if [ -d "$(CORPUS_DIR)/test" ]; then find $(CORPUS_DIR)/test -type l 2>/dev/null | wc -l || echo "0"; else echo "Not split yet"; fi
	@echo ""
	@printf "$(COLOR_BOLD)%-25s$(COLOR_RESET) " "Total size (raw):"
	@du -sh $(CORPUS_DIR)/raw 2>/dev/null | cut -f1 || echo "N/A"
	@printf "$(COLOR_BOLD)%-25s$(COLOR_RESET) " "Total size (all):"
	@du -sh $(CORPUS_DIR) 2>/dev/null | cut -f1 || echo "N/A"
	@echo ""
	@echo "$(COLOR_BOLD)═══════════════════════════════════════════════════$(COLOR_RESET)"
	@echo ""

sample: ## Show random sample of sprite metadata
	@echo "$(COLOR_BLUE)Random sprite samples:$(COLOR_RESET)"
	@echo ""
	@for file in $$(ls $(CORPUS_DIR)/metadata/*.json 2>/dev/null | shuf -n 3); do \
		echo "$(COLOR_BOLD)$$(basename $$file)$(COLOR_RESET)"; \
		$(PYTHON) -c "import json; data=json.load(open('$$file')); print(f\"  Title: {data['title']}\n  Author: {data['author']}\n  Tags: {', '.join(data['tags'][:5])}\n  License: {data['license']}\")"; \
		echo ""; \
	done

clean: ## Remove downloaded sprites (keeps scripts)
	@echo "$(COLOR_YELLOW)Removing corpus data...$(COLOR_RESET)"
	rm -rf $(CORPUS_DIR)/raw/*
	rm -rf $(CORPUS_DIR)/metadata/*
	rm -rf $(CORPUS_DIR)/train/*
	rm -rf $(CORPUS_DIR)/test/*
	rm -f corpus_fetch.log
	@echo "$(COLOR_GREEN)✓ Corpus cleaned$(COLOR_RESET)"

clean-all: clean ## Remove everything including corpus directories
	@echo "$(COLOR_YELLOW)Removing all corpus directories...$(COLOR_RESET)"
	rm -rf $(CORPUS_DIR)
	@echo "$(COLOR_GREEN)✓ Everything cleaned$(COLOR_RESET)"

reset: clean-all setup ## Reset everything and reinstall
	@echo "$(COLOR_GREEN)✓ Reset complete$(COLOR_RESET)"

# Advanced targets

fetch-1k: setup ## Fetch 1,000 sprites
	@$(MAKE) fetch TARGET_COUNT=1000

fetch-5k: setup ## Fetch 5,000 sprites
	@$(MAKE) fetch TARGET_COUNT=5000

export: ## Export corpus info to JSON
	@echo "$(COLOR_BLUE)Exporting corpus information...$(COLOR_RESET)"
	@$(PYTHON) -c "import json, glob; \
		metadata = [json.load(open(f)) for f in glob.glob('$(CORPUS_DIR)/metadata/*.json')]; \
		summary = { \
			'total_sprites': len(metadata), \
			'licenses': list(set(m['license'] for m in metadata)), \
			'sources': list(set(m['source'] for m in metadata)), \
			'authors': len(set(m['author'] for m in metadata)), \
			'total_tags': len(set(tag for m in metadata for tag in m['tags'])) \
		}; \
		json.dump(summary, open('$(CORPUS_DIR)/corpus_summary.json', 'w'), indent=2); \
		print(json.dumps(summary, indent=2))"
	@echo ""
	@echo "$(COLOR_GREEN)✓ Exported to $(CORPUS_DIR)/corpus_summary.json$(COLOR_RESET)"

analyze: ## Analyze corpus content
	@echo "$(COLOR_BLUE)Analyzing corpus...$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_BOLD)Top 10 Authors:$(COLOR_RESET)"
	@$(PYTHON) -c "import json, glob, collections; metadata = [json.load(open(f)) for f in glob.glob('$(CORPUS_DIR)/metadata/*.json')]; authors = collections.Counter(m['author'] for m in metadata); [print(f'  {count:4d}  {author}') for author, count in authors.most_common(10)]"
	@echo ""
	@echo "$(COLOR_BOLD)Top 15 Tags:$(COLOR_RESET)"
	@$(PYTHON) -c "import json, glob, collections; metadata = [json.load(open(f)) for f in glob.glob('$(CORPUS_DIR)/metadata/*.json')]; tags = collections.Counter(tag for m in metadata for tag in m['tags']); [print(f'  {count:4d}  {tag}') for tag, count in tags.most_common(15)]"

check: verify ## Alias for verify

all: setup fetch split stats ## Complete workflow: setup, fetch, split, and show stats

# Default target
.DEFAULT_GOAL := help
