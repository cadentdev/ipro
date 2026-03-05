#!/bin/bash
#
# convert-all.sh - Convert all images in a directory to JPEG format
#
# Usage:
#   ./convert-all.sh <input_dir> [output_dir]
#   ./convert-all.sh ./photos
#   ./convert-all.sh ./photos ./converted
#
# Arguments:
#   input_dir  - Directory containing images to convert
#   output_dir - Optional output directory (default: ./converted/)
#
# What it does:
#   1. Converts all supported image formats to JPEG
#   2. Preserves EXIF metadata by default
#   3. Uses quality setting of 90 (configurable via QUALITY env var)
#
# Example:
#   Input:  photo.heic, image.mpo, pic.png
#   Output: photo.jpg, image.jpg, pic.jpg
#
# Notes:
#   - Creates copies, does not modify originals
#   - Skips files that are already JPEG
#   - Works with HEIC, MPO, PNG, TIFF, WEBP, BMP, GIF, DNG

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMGPRO="$SCRIPT_DIR/../ipro.py"

# Quality setting (can be overridden via environment variable)
QUALITY="${QUALITY:-80}"

# Force re-conversion of existing JPEGs (set via FORCE=1 env var)
FORCE="${FORCE:-0}"

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <input_dir> [output_dir]"
    echo ""
    echo "Arguments:"
    echo "  input_dir  - Directory containing images to convert"
    echo "  output_dir - Optional output directory (default: ./converted/)"
    echo ""
    echo "What it does:"
    echo "  1. Converts all supported image formats to JPEG"
    echo "  2. Preserves EXIF metadata by default"
    echo "  3. Uses quality setting of $QUALITY (set QUALITY env var to change)"
    echo ""
    echo "Examples:"
    echo "  $0 ./photos              # Output to ./converted/"
    echo "  $0 ./photos ./jpegs      # Output to ./jpegs/"
    echo "  QUALITY=95 $0 ./photos   # Use higher quality"
    echo "  FORCE=1 $0 ./photos      # Re-convert existing JPEGs"
    exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIR="${2:-./converted}"

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

echo "Convert All Images to JPEG"
echo "=========================="
echo "Input directory:  $INPUT_DIR"
echo "Output directory: $OUTPUT_DIR"
echo "Quality:          $QUALITY"
if [ "$FORCE" = "1" ]; then
    echo "Force mode:       ON (will re-convert JPEGs)"
fi
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Count files
TOTAL=0
SUCCESS=0
SKIPPED=0
FAILED=0

# Process each image file
for img in "$INPUT_DIR"/*; do
    # Skip directories
    [ -f "$img" ] || continue

    # Skip non-image files (basic extension check)
    img_lower=$(echo "$img" | tr '[:upper:]' '[:lower:]')
    case "$img_lower" in
        *.jpg|*.jpeg|*.png|*.heic|*.heif|*.gif|*.bmp|*.tiff|*.tif|*.webp|*.dng|*.mpo)
            ;;
        *)
            continue
            ;;
    esac

    TOTAL=$((TOTAL + 1))
    FILENAME=$(basename "$img")

    # Check if already a JPEG (skip unless FORCE is set)
    case "$img_lower" in
        *.jpg|*.jpeg)
            if [ "$FORCE" != "1" ]; then
                echo "  $FILENAME (skipped: already JPEG)"
                SKIPPED=$((SKIPPED + 1))
                continue
            fi
            ;;
    esac

    # Run convert command
    OUTPUT=$(python3 "$IMGPRO" convert "$img" --format jpeg --output "$OUTPUT_DIR" --quality "$QUALITY" 2>&1) || true

    if echo "$OUTPUT" | grep -qi "created:"; then
        # Successfully converted
        NEW_FILE=$(echo "$OUTPUT" | grep -i "created:" | sed 's/.*Created: //')
        echo "  $FILENAME -> $(basename "$NEW_FILE")"
        SUCCESS=$((SUCCESS + 1))
    elif echo "$OUTPUT" | grep -qi "error"; then
        # Some error occurred
        echo "  $FILENAME (error: $OUTPUT)" >&2
        FAILED=$((FAILED + 1))
    else
        # Unknown output
        echo "  $FILENAME (unknown: $OUTPUT)" >&2
        FAILED=$((FAILED + 1))
    fi
done

# Summary
echo ""
echo "=========================="
echo "Summary:"
echo "  Total images:  $TOTAL"
echo "  Converted:     $SUCCESS"
echo "  Skipped:       $SKIPPED (already JPEG)"
echo "  Failed:        $FAILED"

if [ $TOTAL -eq 0 ]; then
    echo ""
    echo "No image files found in $INPUT_DIR"
    exit 0
fi

if [ $FAILED -gt 0 ]; then
    echo ""
    echo "Warning: $FAILED files failed to convert."
    exit 1
fi
