# ipro Batch Scripts

Utility scripts for batch image processing workflows using `ipro`.

## Scripts Overview

| Script | Purpose |
|--------|---------|
| `rename-all.sh` | Add EXIF date prefix and correct file extensions |
| `convert-all.sh` | Convert images to JPEG with sRGB color profile |
| `resize-all.sh` | Resize images to specified width(s) |
| `prepare-instagram.sh` | Validate aspect ratios, resize to 1080px, convert to Instagram-ready JPEG |
| `organize-by-orientation.sh` | Organize images by orientation or aspect ratio |
| `organize-by-date.sh` | Organize images into subdirectories by ISO date prefix |
| `organize-all-by-date.sh` | Run `organize-by-date.sh` on all subdirectories |

## Prerequisites

- Python 3.8+ with virtual environment activated
- ipro dependencies installed (`pip install -r requirements.txt`)

```bash
# Activate virtual environment
source .venv/bin/activate
```

---

## rename-all.sh

Rename all images with EXIF date prefix and correct file extension.

### Usage

```bash
./scripts/rename-all.sh <input_dir> [output_dir]
```

### What it does

1. Adds EXIF date prefix (`YYYY-MM-DDTHHMMSS_`) to each filename
2. Corrects file extension based on actual image format
3. Skips files without EXIF date (with warning)

### Examples

```bash
# Rename images in place
./scripts/rename-all.sh ./photos

# Output to different directory
./scripts/rename-all.sh ./photos ./renamed
```

### Sample Output

```
Input:  photo.HEIC (actually JPEG, taken 2024-11-12 14:30:00)
Output: 2024-11-12T143000_photo.jpg
```

---

## convert-all.sh

Convert all images to JPEG format with sRGB color profile.

### Usage

```bash
./scripts/convert-all.sh <input_dir> [output_dir]
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `QUALITY` | 80 | JPEG quality (1-100) |
| `FORCE` | 0 | Set to `1` to re-convert existing JPEGs |

### Examples

```bash
# Convert all images to JPEG
./scripts/convert-all.sh ./photos ./converted

# Use higher quality
QUALITY=95 ./scripts/convert-all.sh ./photos

# Force re-convert existing JPEGs (apply sRGB profile)
FORCE=1 ./scripts/convert-all.sh ./photos ./final
```

### Supported Input Formats

- HEIC/HEIF (iPhone photos)
- PNG, TIFF, BMP, GIF, WebP
- MPO (multi-picture object)
- DNG (Adobe Digital Negative)

---

## resize-all.sh

Resize all JPEG images to specified width(s).

### Usage

```bash
./scripts/resize-all.sh <input_dir> <width> [output_dir]
```

### Arguments

- `input_dir` - Directory containing images to resize
- `width` - Target width(s), comma-separated (e.g., `1080` or `300,600,1080`)
- `output_dir` - Optional output directory (default: `./resized/`)

### Examples

```bash
# Resize to single width
./scripts/resize-all.sh ./photos 1080

# Resize to multiple widths for srcset
./scripts/resize-all.sh ./photos 300,600,1080 ./web-images
```

### Notes

- Only processes JPEG files (ipro resize limitation)
- Skips files already smaller than target width (no upscaling)
- Output files are named `{basename}_{width}.jpg`

---

## prepare-instagram.sh

Prepare images for Instagram and social media posting with aspect ratio validation, resizing, and format optimization.

### Usage

```bash
./scripts/prepare-instagram.sh <input_dir>
```

### What it does

1. **Validates all images have the same aspect ratio** - Exits with error if mismatched
2. **Resizes to 1080px wide** at 95% quality (high-quality intermediate)
3. **Converts to final JPEG** at 80% quality with sRGB color profile

### Arguments

- `input_dir` - Directory containing images to process (e.g., `img/mlkb-01-square`)

### Output Directories

The script creates two parallel output directories at the same level as the input:

- `{input_dir}-1-resized/` - Resized images (1080px wide, 95% quality)
- `{input_dir}-2-final/` - Final Instagram-ready images (80% quality, sRGB)

### Examples

```bash
# Process square images for Instagram
./scripts/prepare-instagram.sh img/mlkb-01-square

# Process landscape images (16:9)
./scripts/prepare-instagram.sh img/vacation-landscape

# Check output
ls img/mlkb-01-square-2-final/
```

### Sample Output

```
Instagram Image Preparation
============================
Input directory: img/mlkb-01-square

Step 1: Checking aspect ratios...
-----------------------------------
Found 10 image(s)
Reference aspect ratio: 1:1 (from photo1.jpg)

  ✓ photo1.jpg (1:1)
  ✓ photo2.jpg (1:1)
  ...

✓ All images have matching aspect ratio: 1:1

Step 2: Resizing to 1080px wide...
-----------------------------------
Output directory: img/mlkb-01-square-1-resized
Quality: 95%

Processing: photo1.jpg (1536x1536)
✓ Created: photo1_1080.jpg (1080x1080, 478 KB)
...

Resize summary:
  Resized:  10
  Copied:   0 (already smaller than target)
  Failed:   0

Step 3: Converting to JPEG with sRGB...
-----------------------------------
Input directory:  img/mlkb-01-square-1-resized
Output directory: img/mlkb-01-square-2-final
Quality: 80%
Color profile: sRGB

Converting: photo1_1080.jpg
...

Convert summary:
  Converted: 10
  Failed:    0

============================
✓ Instagram preparation complete!

Output directories:
  Resized: img/mlkb-01-square-1-resized (1080px wide, 95% quality)
  Final:   img/mlkb-01-square-2-final (80% quality, sRGB)

Directory sizes:
  Original:  11M
  Resized:  4.2M
  Final:    2.1M

Ready to upload images from: img/mlkb-01-square-2-final
```

### Features

- **Aspect ratio validation** - Works with any aspect ratio (1:1, 16:9, 4:3, etc.), not just square images
- **Non-destructive** - Original files are never modified
- **Two-stage processing** - Maintains quality through resize, then applies final compression
- **Smart file handling** - Only processes valid image files, ignores subdirectories
- **Parallel output directories** - Easy to compare file sizes at each stage
- **Fail-fast** - Exits immediately if aspect ratios don't match or processing fails

### Instagram Specifications

This script produces images optimized for Instagram's current recommendations:

- **Resolution**: 1080px (Instagram's standard display width)
- **Format**: JPEG with sRGB color profile
- **Quality**: 80% (balances quality and file size)
- **Aspect ratio**: Must be consistent across all images in a set

### Notes

- Images smaller than 1080px will be copied at original size (no upscaling)
- EXIF metadata is stripped from final output
- Color profile is converted to sRGB for consistent display across devices
- The two-stage process (resize → convert) maintains maximum quality

---

## organize-by-orientation.sh

Organize images into subdirectories by orientation or aspect ratio.

### Usage

```bash
./scripts/organize-by-orientation.sh <input_dir> [output_dir] [--by-ratio]
```

### Modes

**By Orientation (default):**
Creates `landscape/`, `portrait/`, `square/` subdirectories.

**By Aspect Ratio (`--by-ratio`):**
Creates subdirectories like `16x9/`, `4x3/`, `3x4/`, `1x1/`, `other/`.

### Examples

```bash
# Organize by orientation
./scripts/organize-by-orientation.sh ./photos

# Organize by aspect ratio to different directory
./scripts/organize-by-orientation.sh ./photos ./organized --by-ratio
```

### Sample Output

```
Created directories:
  4x3/: 89 files
  3x4/: 46 files
  other/: 13 files
```

---

## organize-by-date.sh

Organize images into subdirectories based on their ISO date prefix (e.g., `2025-10-17`).

### Usage

```bash
./scripts/organize-by-date.sh [directory]
```

### Arguments

- `directory` - Directory containing images to organize (default: current directory)

### What it does

1. Finds files starting with `2025-` (ISO date format)
2. Extracts the first 10 characters as the date (e.g., `2025-10-17`)
3. Creates a subdirectory with that date name
4. Moves the file into the corresponding date subdirectory

### Examples

```bash
# Organize files in current directory
./scripts/organize-by-date.sh

# Organize files in specific directory
./scripts/organize-by-date.sh ./photos
```

### Sample Output

```
Moved: 2025-10-17T095346_photo.jpg -> 2025-10-17/
Moved: 2025-10-17T101030_IMG_3749.jpg -> 2025-10-17/
Moved: 2025-10-19T151734_photo2.jpg -> 2025-10-19/
```

### Notes

- Only processes files (skips directories)
- Files must start with `2025-` to be organized
- Creates date subdirectories automatically

---

## organize-all-by-date.sh

Run `organize-by-date.sh` on all subdirectories within a parent directory.

### Usage

```bash
./scripts/organize-all-by-date.sh <parent_directory>
```

### Arguments

- `parent_directory` - Directory containing subdirectories to process

### What it does

1. Iterates through all subdirectories in the parent directory
2. Runs `organize-by-date.sh` in each subdirectory
3. Reports progress for each subdirectory processed

### Examples

```bash
# Organize all subdirectories in img/organized
./scripts/organize-all-by-date.sh ./img/organized
```

### Sample Output

```
=== Processing: ./img/organized/3x4/ ===
Moved: 2025-10-16T095029_photo.jpg -> 2025-10-16/
Moved: 2025-10-17T095346_photo.jpg -> 2025-10-17/
=== Processing: ./img/organized/4x3/ ===
Moved: 2025-10-18T120000_photo.jpg -> 2025-10-18/
=== Done ===
```

### Notes

- Validates that the parent directory exists before processing
- Useful after organizing images by orientation/ratio with `organize-by-orientation.sh`

---

## Complete Workflow Example

A typical image processing pipeline from the devlog:

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Rename with EXIF dates and correct extensions
./scripts/rename-all.sh img/originals img/renamed

# 3. Convert to JPEG with sRGB profile (80% quality)
./scripts/convert-all.sh img/renamed img/converted

# 4. Resize to web-friendly dimensions
./scripts/resize-all.sh img/converted 1080 img/final

# 5. Organize by aspect ratio
./scripts/organize-by-orientation.sh img/final img/organized --by-ratio
```

### Results from Real Usage

| Stage | Size | Reduction |
|-------|------|-----------|
| Original | 161 MB | — |
| Converted (80% JPEG, sRGB) | 100 MB | 38% smaller |
| Resized to 1080px | 39 MB | **76% smaller** |

---

## Notes

- All scripts create copies (non-destructive)
- Scripts use `set -e` for fail-fast behavior
- Compatible with macOS and Linux (uses POSIX-compatible shell syntax)
