#!/bin/bash
#
# organize-by-orientation.sh - Organize images by orientation or aspect ratio
#
# Usage:
#   ./organize-by-orientation.sh <input_dir> [output_dir] [--by-ratio]
#   ./organize-by-orientation.sh ./photos
#   ./organize-by-orientation.sh ./photos ./organized --by-ratio
#
# Arguments:
#   input_dir  - Directory containing images to organize
#   output_dir - Optional: output directory for organized files (default: same as input_dir)
#   --by-ratio - Optional: organize by aspect ratio instead of orientation
#
# Output structure (default - by orientation):
#   input_dir/
#     landscape/
#     portrait/
#     square/
#
# Output structure (--by-ratio):
#   input_dir/
#     16x9/
#     4x3/
#     1x1/
#     other/
#
# Notes:
#   - Creates copies, does not move originals
#   - Works with any image format Pillow supports

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMGPRO="$SCRIPT_DIR/../ipro.py"

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <input_dir> [output_dir] [--by-ratio]"
    echo ""
    echo "Arguments:"
    echo "  input_dir  - Directory containing images to organize"
    echo "  output_dir - Optional: output directory (default: same as input_dir)"
    echo "  --by-ratio - Optional: organize by aspect ratio instead of orientation"
    echo ""
    echo "Examples:"
    echo "  $0 ./photos                       # Organize into landscape/portrait/square"
    echo "  $0 ./photos ./organized           # Output to different directory"
    echo "  $0 ./photos ./organized --by-ratio # Organize by ratio into different directory"
    exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIR=""
BY_RATIO=false

# Parse remaining arguments
shift
for arg in "$@"; do
    if [ "$arg" = "--by-ratio" ]; then
        BY_RATIO=true
    elif [ -z "$OUTPUT_DIR" ]; then
        OUTPUT_DIR="$arg"
    fi
done

# Default output to input directory if not specified
if [ -z "$OUTPUT_DIR" ]; then
    OUTPUT_DIR="$INPUT_DIR"
fi

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

if [ "$BY_RATIO" = true ]; then
    MODE="Aspect Ratio"
else
    MODE="Orientation"
fi

echo "Organize Images by $MODE"
echo "========================================"
echo "Input directory: $INPUT_DIR"
echo "Mode: $MODE"
echo ""

# Count files
TOTAL=0
SUCCESS=0
FAILED=0

# Process each image file
for img in "$INPUT_DIR"/*; do
    # Skip directories
    [ -f "$img" ] || continue

    # Skip non-image files (basic extension check)
    # Use tr for lowercase conversion (compatible with all shells)
    img_lower=$(echo "$img" | tr '[:upper:]' '[:lower:]')
    case "$img_lower" in
        *.jpg|*.jpeg|*.png|*.heic|*.heif|*.gif|*.bmp|*.tiff|*.webp)
            ;;
        *)
            continue
            ;;
    esac

    TOTAL=$((TOTAL + 1))
    FILENAME=$(basename "$img")

    # Get image info as JSON
    INFO=$(python3 "$IMGPRO" info "$img" --json 2>/dev/null) || {
        echo "Warning: Could not read $FILENAME, skipping" >&2
        FAILED=$((FAILED + 1))
        continue
    }

    if [ "$BY_RATIO" = true ]; then
        # Extract common_ratio from JSON
        RATIO=$(echo "$INFO" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('common_ratio', 'none'))" 2>/dev/null)

        if [ "$RATIO" = "none" ] || [ -z "$RATIO" ]; then
            DEST_DIR="$OUTPUT_DIR/other"
        else
            # Convert ratio format: "16:9" -> "16x9" (no colons in dir names)
            RATIO_DIR=$(echo "$RATIO" | tr ':' 'x')
            DEST_DIR="$OUTPUT_DIR/$RATIO_DIR"
        fi
    else
        # Extract orientation from JSON
        ORIENTATION=$(echo "$INFO" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('orientation', 'unknown'))" 2>/dev/null)

        if [ -z "$ORIENTATION" ] || [ "$ORIENTATION" = "unknown" ]; then
            echo "Warning: Could not determine orientation for $FILENAME, skipping" >&2
            FAILED=$((FAILED + 1))
            continue
        fi

        DEST_DIR="$OUTPUT_DIR/$ORIENTATION"
    fi

    # Create destination directory if needed
    mkdir -p "$DEST_DIR"

    # Copy file to destination
    if cp "$img" "$DEST_DIR/$FILENAME"; then
        echo "  $FILENAME -> $DEST_DIR/"
        SUCCESS=$((SUCCESS + 1))
    else
        echo "Warning: Failed to copy $FILENAME" >&2
        FAILED=$((FAILED + 1))
    fi
done

# Summary
echo ""
echo "========================================"
echo "Summary:"
echo "  Total images: $TOTAL"
echo "  Organized:    $SUCCESS"
echo "  Failed:       $FAILED"

if [ $TOTAL -eq 0 ]; then
    echo ""
    echo "No image files found in $INPUT_DIR"
    exit 0
fi

# List created directories
echo ""
echo "Created directories:"
if [ "$BY_RATIO" = true ]; then
    for dir in "$INPUT_DIR"/*/; do
        [ -d "$dir" ] || continue
        COUNT=$(ls -1 "$dir" 2>/dev/null | wc -l)
        echo "  $(basename "$dir")/: $COUNT files"
    done
else
    for orientation in landscape portrait square; do
        if [ -d "$INPUT_DIR/$orientation" ]; then
            COUNT=$(ls -1 "$INPUT_DIR/$orientation" 2>/dev/null | wc -l)
            echo "  $orientation/: $COUNT files"
        fi
    done
fi
