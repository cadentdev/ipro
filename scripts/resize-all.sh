#!/bin/bash
#
# resize-all.sh - Resize all images in a directory to specified width(s)
#
# Usage:
#   ./resize-all.sh <input_dir> <width> [output_dir]
#   ./resize-all.sh ./photos 1080
#   ./resize-all.sh ./photos 300,600,1080 ./resized
#
# Arguments:
#   input_dir  - Directory containing images to resize
#   width      - Target width(s), comma-separated (e.g., "1080" or "300,600,1080")
#   output_dir - Optional output directory (default: ./resized/)
#
# Notes:
#   - Only processes JPEG files (ipro resize limitation)
#   - Skips files that are already smaller than target width
#   - Uses || true to continue on errors

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMGPRO="$SCRIPT_DIR/../ipro.py"

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 <input_dir> <width> [output_dir]"
    echo ""
    echo "Arguments:"
    echo "  input_dir  - Directory containing images to resize"
    echo "  width      - Target width(s), comma-separated (e.g., '1080' or '300,600,1080')"
    echo "  output_dir - Optional output directory (default: ./resized/)"
    echo ""
    echo "Examples:"
    echo "  $0 ./photos 1080"
    echo "  $0 ./photos 300,600,1080 ./web-images"
    exit 1
fi

INPUT_DIR="$1"
WIDTH="$2"
OUTPUT_DIR="${3:-./resized/}"

# Validate input directory
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory not found: $INPUT_DIR" >&2
    exit 1
fi

# Check if ipro.py exists
if [ ! -f "$IMGPRO" ]; then
    echo "Error: ipro.py not found at: $IMGPRO" >&2
    exit 1
fi

# Create output directory if needed
mkdir -p "$OUTPUT_DIR"

echo "Resize All Images"
echo "================="
echo "Input directory: $INPUT_DIR"
echo "Target width(s): $WIDTH"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Count files
TOTAL=0
SUCCESS=0
SKIPPED=0
FAILED=0

# Process each JPEG file
for img in "$INPUT_DIR"/*.jpg "$INPUT_DIR"/*.jpeg "$INPUT_DIR"/*.JPG "$INPUT_DIR"/*.JPEG; do
    # Skip if no matches (glob didn't expand)
    [ -e "$img" ] || continue

    TOTAL=$((TOTAL + 1))
    FILENAME=$(basename "$img")

    echo "Processing: $FILENAME"

    if python3 "$IMGPRO" resize "$img" --width "$WIDTH" --output "$OUTPUT_DIR" 2>&1; then
        SUCCESS=$((SUCCESS + 1))
    else
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 0 ]; then
            # All sizes skipped (upscaling prevention)
            SKIPPED=$((SKIPPED + 1))
        else
            echo "  Warning: Failed to process $FILENAME" >&2
            FAILED=$((FAILED + 1))
        fi
    fi
    echo ""
done

# Summary
echo "================="
echo "Summary:"
echo "  Total files: $TOTAL"
echo "  Successful:  $SUCCESS"
echo "  Skipped:     $SKIPPED"
echo "  Failed:      $FAILED"

if [ $TOTAL -eq 0 ]; then
    echo ""
    echo "No JPEG files found in $INPUT_DIR"
    exit 0
fi
