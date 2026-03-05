#!/bin/bash
#
# prepare-instagram.sh - Prepare images for Instagram/social media posting
#
# Usage:
#   ./prepare-instagram.sh <input_dir>
#   ./prepare-instagram.sh img/mlkb-01-square
#
# Arguments:
#   input_dir  - Directory containing images to process
#
# What it does:
#   1. Validates all images have the same aspect ratio
#   2. Resizes all images to 1080px wide at 95% quality
#   3. Converts to JPEG at 80% quality with sRGB color profile
#
# Output directories (created at same level as input):
#   {input_dir}-1-resized/  - Resized images (1080px wide, 95% quality)
#   {input_dir}-2-final/    - Final Instagram-ready images (80% quality, sRGB)
#
# Notes:
#   - Non-destructive: Original files are never modified
#   - Only processes image files (skips directories and non-images)
#   - Exits with error if images have different aspect ratios

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMGPRO="$SCRIPT_DIR/../ipro.py"

# Default settings
RESIZE_WIDTH="1080"
RESIZE_QUALITY="95"
FINAL_QUALITY="80"

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <input_dir>"
    echo ""
    echo "Arguments:"
    echo "  input_dir  - Directory containing images to process"
    echo ""
    echo "What it does:"
    echo "  1. Validates all images have the same aspect ratio"
    echo "  2. Resizes all images to ${RESIZE_WIDTH}px wide at ${RESIZE_QUALITY}% quality"
    echo "  3. Converts to JPEG at ${FINAL_QUALITY}% quality with sRGB color profile"
    echo ""
    echo "Example:"
    echo "  $0 img/mlkb-01-square"
    echo ""
    echo "Output directories:"
    echo "  {input_dir}-1-resized/  - Resized images"
    echo "  {input_dir}-2-final/    - Final Instagram-ready images"
    exit 1
fi

INPUT_DIR="$1"

# Remove trailing slash from input directory for consistent naming
INPUT_DIR="${INPUT_DIR%/}"

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

echo "Instagram Image Preparation"
echo "============================"
echo "Input directory: $INPUT_DIR"
echo ""

# Step 1: Check aspect ratios
echo "Step 1: Checking aspect ratios..."
echo "-----------------------------------"

# Collect all image files
IMAGE_FILES=()
for img in "$INPUT_DIR"/*; do
    # Skip directories
    [ -f "$img" ] || continue

    # Check if it's an image file by trying to get info
    if python3 "$IMGPRO" info "$img" --json &>/dev/null; then
        IMAGE_FILES+=("$img")
    fi
done

# Check if we found any images
if [ ${#IMAGE_FILES[@]} -eq 0 ]; then
    echo "Error: No valid image files found in $INPUT_DIR" >&2
    exit 1
fi

echo "Found ${#IMAGE_FILES[@]} image(s)"

# Get aspect ratio from first image
FIRST_IMAGE="${IMAGE_FILES[0]}"
FIRST_RATIO=$(python3 "$IMGPRO" info "$FIRST_IMAGE" --json | python3 -c "import sys, json; print(json.load(sys.stdin)['ratio_raw'])")

echo "Reference aspect ratio: $FIRST_RATIO (from $(basename "$FIRST_IMAGE"))"
echo ""

# Check all other images have the same aspect ratio
ASPECT_RATIO_MISMATCH=0
for img in "${IMAGE_FILES[@]}"; do
    FILENAME=$(basename "$img")
    RATIO=$(python3 "$IMGPRO" info "$img" --json | python3 -c "import sys, json; print(json.load(sys.stdin)['ratio_raw'])")

    if [ "$RATIO" != "$FIRST_RATIO" ]; then
        echo "  ERROR: $FILENAME has aspect ratio $RATIO (expected $FIRST_RATIO)" >&2
        ASPECT_RATIO_MISMATCH=1
    else
        echo "  ✓ $FILENAME ($RATIO)"
    fi
done

if [ $ASPECT_RATIO_MISMATCH -eq 1 ]; then
    echo ""
    echo "Error: Not all images have the same aspect ratio!" >&2
    echo "All images must have matching aspect ratios to continue." >&2
    exit 1
fi

echo ""
echo "✓ All images have matching aspect ratio: $FIRST_RATIO"
echo ""

# Step 2: Resize images
RESIZE_DIR="${INPUT_DIR}-1-resized"
echo "Step 2: Resizing to ${RESIZE_WIDTH}px wide..."
echo "-----------------------------------"
echo "Output directory: $RESIZE_DIR"
echo "Quality: ${RESIZE_QUALITY}%"
echo ""

# Create resize output directory
mkdir -p "$RESIZE_DIR"

RESIZE_SUCCESS=0
RESIZE_SKIPPED=0
RESIZE_FAILED=0

for img in "${IMAGE_FILES[@]}"; do
    FILENAME=$(basename "$img")
    echo "Processing: $FILENAME"

    if python3 "$IMGPRO" resize "$img" --width "$RESIZE_WIDTH" --output "$RESIZE_DIR" --quality "$RESIZE_QUALITY" 2>&1; then
        RESIZE_SUCCESS=$((RESIZE_SUCCESS + 1))
    else
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 0 ]; then
            # Size skipped (image already smaller than target)
            RESIZE_SKIPPED=$((RESIZE_SKIPPED + 1))
            # Copy original to resize dir if it was skipped
            cp "$img" "$RESIZE_DIR/"
            echo "  Note: Image smaller than ${RESIZE_WIDTH}px, copied original"
        else
            echo "  Error: Failed to resize $FILENAME" >&2
            RESIZE_FAILED=$((RESIZE_FAILED + 1))
        fi
    fi
done

echo ""
echo "Resize summary:"
echo "  Resized:  $RESIZE_SUCCESS"
echo "  Copied:   $RESIZE_SKIPPED (already smaller than target)"
echo "  Failed:   $RESIZE_FAILED"

if [ $RESIZE_FAILED -gt 0 ]; then
    echo ""
    echo "Error: Some images failed to resize. Cannot continue." >&2
    exit 1
fi

echo ""

# Step 3: Convert to final format
FINAL_DIR="${INPUT_DIR}-2-final"
echo "Step 3: Converting to JPEG with sRGB..."
echo "-----------------------------------"
echo "Input directory:  $RESIZE_DIR"
echo "Output directory: $FINAL_DIR"
echo "Quality: ${FINAL_QUALITY}%"
echo "Color profile: sRGB"
echo ""

# Create final output directory
mkdir -p "$FINAL_DIR"

CONVERT_SUCCESS=0
CONVERT_FAILED=0

# Process all files from resize directory
for img in "$RESIZE_DIR"/*; do
    # Skip if not a file
    [ -f "$img" ] || continue

    FILENAME=$(basename "$img")
    echo "Converting: $FILENAME"

    if python3 "$IMGPRO" convert "$img" --format jpeg --output "$FINAL_DIR" --quality "$FINAL_QUALITY" 2>&1 | grep -q "Created:"; then
        CONVERT_SUCCESS=$((CONVERT_SUCCESS + 1))
    else
        echo "  Error: Failed to convert $FILENAME" >&2
        CONVERT_FAILED=$((CONVERT_FAILED + 1))
    fi
done

echo ""
echo "Convert summary:"
echo "  Converted: $CONVERT_SUCCESS"
echo "  Failed:    $CONVERT_FAILED"

if [ $CONVERT_FAILED -gt 0 ]; then
    echo ""
    echo "Error: Some images failed to convert." >&2
    exit 1
fi

echo ""
echo "============================"
echo "✓ Instagram preparation complete!"
echo ""
echo "Output directories:"
echo "  Resized: $RESIZE_DIR (${RESIZE_WIDTH}px wide, ${RESIZE_QUALITY}% quality)"
echo "  Final:   $FINAL_DIR (${FINAL_QUALITY}% quality, sRGB)"
echo ""

# Show total file sizes for comparison
if command -v du &> /dev/null; then
    ORIG_SIZE=$(du -sh "$INPUT_DIR" | cut -f1)
    RESIZE_SIZE=$(du -sh "$RESIZE_DIR" | cut -f1)
    FINAL_SIZE=$(du -sh "$FINAL_DIR" | cut -f1)

    echo "Directory sizes:"
    echo "  Original: $ORIG_SIZE"
    echo "  Resized:  $RESIZE_SIZE"
    echo "  Final:    $FINAL_SIZE"
fi

echo ""
echo "Ready to upload images from: $FINAL_DIR"
