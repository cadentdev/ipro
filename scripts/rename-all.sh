#!/bin/bash
#
# rename-all.sh - Rename all images with EXIF date prefix and correct extension
#
# Usage:
#   ./rename-all.sh <input_dir> [output_dir]
#   ./rename-all.sh ./photos
#   ./rename-all.sh ./photos ./renamed
#
# Arguments:
#   input_dir  - Directory containing images to rename
#   output_dir - Optional output directory (default: same as input_dir)
#
# What it does:
#   1. Adds EXIF date prefix (YYYY-MM-DDTHHMMSS_) to each filename
#   2. Corrects file extension based on actual image format
#   3. Skips files without EXIF date (with warning)
#
# Example:
#   Input:  photo.HEIC (actually JPEG, taken 2024-11-12 14:30:00)
#   Output: 2024-11-12T143000_photo.jpg
#
# Notes:
#   - Creates copies, does not modify originals
#   - Works with any image format Pillow supports
#   - Files without EXIF date are skipped (not copied)

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMGPRO="$SCRIPT_DIR/../ipro.py"

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <input_dir> [output_dir]"
    echo ""
    echo "Arguments:"
    echo "  input_dir  - Directory containing images to rename"
    echo "  output_dir - Optional output directory (default: same as input_dir)"
    echo ""
    echo "What it does:"
    echo "  1. Adds EXIF date prefix (YYYY-MM-DDTHHMMSS_) to each filename"
    echo "  2. Corrects file extension based on actual image format"
    echo "  3. Skips files without EXIF date (with warning)"
    echo ""
    echo "Examples:"
    echo "  $0 ./photos              # Rename in place"
    echo "  $0 ./photos ./renamed    # Output to different directory"
    exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIR="${2:-}"

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

echo "Rename All Images"
echo "================="
echo "Input directory: $INPUT_DIR"
if [ -n "$OUTPUT_DIR" ]; then
    echo "Output directory: $OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR"
else
    echo "Output directory: (same as input)"
fi
echo ""

# Count files
TOTAL=0
SUCCESS=0
SKIPPED=0
FAILED=0

# Build output argument
OUTPUT_ARG=""
if [ -n "$OUTPUT_DIR" ]; then
    OUTPUT_ARG="--output $OUTPUT_DIR"
fi

# Process each image file
for img in "$INPUT_DIR"/*; do
    # Skip directories
    [ -f "$img" ] || continue

    # Skip non-image files (basic extension check)
    # Use tr for lowercase conversion (compatible with all shells)
    img_lower=$(echo "$img" | tr '[:upper:]' '[:lower:]')
    case "$img_lower" in
        *.jpg|*.jpeg|*.png|*.heic|*.heif|*.gif|*.bmp|*.tiff|*.webp|*.dng)
            ;;
        *)
            continue
            ;;
    esac

    TOTAL=$((TOTAL + 1))
    FILENAME=$(basename "$img")

    # Run rename with both --ext and --prefix-exif-date
    OUTPUT=$(python3 "$IMGPRO" rename "$img" --ext --prefix-exif-date $OUTPUT_ARG 2>&1) || true
    EXIT_CODE=$?

    if echo "$OUTPUT" | grep -qi "created:"; then
        # Successfully renamed
        NEW_FILE=$(echo "$OUTPUT" | grep -i "created:" | sed 's/.*Created: //')
        echo "  $FILENAME -> $(basename "$NEW_FILE")"
        SUCCESS=$((SUCCESS + 1))
    elif echo "$OUTPUT" | grep -qi "no exif date"; then
        # Skipped due to no EXIF date
        echo "  $FILENAME (skipped: no EXIF date)"
        SKIPPED=$((SKIPPED + 1))
    elif echo "$OUTPUT" | grep -qi "no change"; then
        # No change needed
        echo "  $FILENAME (no change needed)"
        SUCCESS=$((SUCCESS + 1))
    else
        # Some other error
        echo "  $FILENAME (error: $OUTPUT)" >&2
        FAILED=$((FAILED + 1))
    fi
done

# Summary
echo ""
echo "================="
echo "Summary:"
echo "  Total images:  $TOTAL"
echo "  Renamed:       $SUCCESS"
echo "  Skipped:       $SKIPPED (no EXIF date)"
echo "  Failed:        $FAILED"

if [ $TOTAL -eq 0 ]; then
    echo ""
    echo "No image files found in $INPUT_DIR"
    exit 0
fi

if [ $SKIPPED -gt 0 ]; then
    echo ""
    echo "Note: $SKIPPED files were skipped because they have no EXIF date."
    echo "These files were not copied to the output directory."
fi
