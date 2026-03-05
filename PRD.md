# Product Requirements Document: Responsive Image Resizer

**Version:** 1.2
**Date:** December 6, 2025
**Status:** Draft  

---

## 1. Executive Summary

A command-line tool for generating multiple resolutions of images to support responsive web design workflows, specifically for static site generators like 11ty. The tool enables developers to create `srcset`-ready images from source files with configurable dimensions and quality settings.

### Primary Use Case
Generate thumbnail and full-resolution variants of images for lightbox galleries and responsive image displays, creating multiple width-based resolutions from a single source image.

---

## 2. Goals & Objectives

### Goals
- Simplify the creation of responsive image sets for web development
- Provide a scriptable, automation-friendly CLI tool
- Support modern web image optimization workflows
- Enable batch processing through standard Unix pipelines

### Non-Goals (Future Versions)
- Real-time image processing
- GUI or web interface (covered in separate PRD section)
- Advanced image manipulation (filters, effects, compositing)
- Cloud storage integration

### Core Principle: Non-Destructive by Default
All commands that modify or transform images create copies by default, preserving the original file. This ensures:
- User data is never accidentally destroyed
- Easy comparison between original and processed files
- Safe batch processing without risk of data loss

Future versions may add an `--in-place` option to override this behavior for users who explicitly want to modify originals.

---

## 3. User Personas

### Primary: Web Developer
- Works with static site generators (11ty, Hugo, Jekyll)
- Needs to generate responsive image sets regularly
- Comfortable with command-line tools
- Values automation and scriptability

### Secondary: Content Manager
- Prepares images for web publishing
- May use the tool through wrapper scripts
- Needs consistent, predictable output
 
### Tertiary: Social Media Manager
- Manages content for platforms like Instagram, TikTok, and Facebook
- Needs to understand which images are landscape, portrait, or square
- Needs to quickly see aspect ratios and dimensions to comply with platform constraints
- Comfortable using shell scripts to batch-inspect large folders of images
- Uses CSV/JSON reports (from `ipro info`) to group and select images for posts and carousels

---

## 4. Functional Requirements

### 4.1 Image Information (`ipro info`)

- **Requirement:** Inspect a single image file and report key metadata, orientation, and aspect ratio for scripting and analysis.
- **Acceptance Criteria:**
  - **Input:**
    - Accept a required positional `<filepath>` argument: `ipro info <file> [options]`.
    - Support absolute and relative paths.
    - Validate that the file exists and is readable; otherwise print `Error: File not found: <path>` and exit with a non-zero status.
    - Attempt to open the file with Pillow; if Pillow cannot open it (e.g., non-image or unsupported format like MP4), print a clear "unsupported or unreadable image format" error and exit with a non-zero status.
  - **Pixel metadata:**
    - Read the image's pixel dimensions (`width`, `height`), taking EXIF orientation into account so that reported dimensions match the displayed orientation.
    - Classify orientation as `portrait`, `landscape`, or `square` based on effective `width` and `height`.
    - Compute the reduced integer aspect ratio `ratio_raw` (e.g., `4:3`) using the greatest common divisor of width and height.
    - Match `ratio_raw` against a set of common aspect ratios using **exact integer matches only**, including at minimum:
      - `1:1`, `4:3`, `3:2`, `16:9`, `5:4`, `4:5`, `9:16`, `1.91:1` (implemented via an appropriate integer pair such as `191:100`).
    - Expose the detected common ratio as `common_ratio` (string) or `none` if there is no exact match.
  - **File metadata:**
    - Report file name, path, and file size in kilobytes (KB).
  - **EXIF metadata:**
    - Detect whether EXIF data is present.
    - When available, extract a **curated subset** including:
      - Date and time the photo was taken (prefer `DateTimeOriginal`; fall back to sensible alternatives such as `DateTime`).
      - Camera make and model.
      - Orientation tag.
      - Resolution/DPI fields when available (`XResolution`, `YResolution`, `ResolutionUnit`).
    - Expose this curated subset by default in both human-readable and JSON output.
    - Provide an `--exif-all` flag that outputs all EXIF tags as name/value pairs.
  - **Output formats:**
    - **Default (human-readable):**
      - Print a multi-line summary suitable for terminal use, including file info, pixel dimensions, orientation, aspect ratio, and a short EXIF summary.
    - **`--json`:**
      - Print a single JSON object per invocation to stdout.
      - JSON must include, at minimum: filename, path, width, height, orientation, `ratio_raw`, `common_ratio`, file size (KB), a boolean for EXIF presence, creation date (if known), curated EXIF fields, and full EXIF data when `--exif-all` is specified.
    - **`--short`:**
      - Print a single comma-separated line (CSV) per invocation to stdout.
      - Fields should be in a stable, documented order such as:
        - `filename,width,height,orientation,ratio_raw,common_ratio,size_kb,creation_date`
      - Designed for use with shell loops for quick CSV generation, for example:
        - `for img in *.jpg; do ipro info "$img" --short >> info.csv; done`
  - **Custom field selection:**
    - Individual field flags allow selective output of specific metadata:
      - `--width` or `-w`: Output only width value
      - `--height` or `-h`: Output only height value
      - `--format`: Output only file format
      - `--aspect-ratio`: Output only aspect ratio
      - `--orientation`: Output only orientation
    - When multiple field flags are combined, values are space-separated by default.
    - Field selection can be combined with output format flags:
      - Default: space-separated values (e.g., `1920 1080 JPEG`)
      - `--csv`: comma-separated values (e.g., `1920,1080,JPEG`)
      - `--json`: JSON object with field names (e.g., `{"width": 1920, "height": 1080, "format": "JPEG", "filename": "photo.jpg"}`)
      - `--key-value`: key-value pairs (e.g., `width: 1920, height: 1080, format: JPEG`)
    - JSON output always includes `filename` for identification.
  - **Format support:**
    - `ipro info` must support **any image format that the installed Pillow build can open**, including but not limited to JPEG, PNG, HEIF/HEIC, and certain RAW formats.
    - Non-image files and unsupported formats (e.g., MP4) must fail with a clear error and non-zero exit code.

### 4.2 Image Resizing (`ipro resize`)

- **Requirement:** Resize images to specified dimensions while maintaining aspect ratio, without upscaling.
- **Acceptance Criteria:**
  - **Invocation:**
    - Support subcommand syntax: `ipro resize <file> [options]`.
    - `<file>` is a required positional argument referring to the source image.
  - **Resize parameters:**
    - Support `--width <sizes>` with a comma-separated list of integer target widths.
    - Support `--height <sizes>` with a comma-separated list of integer target heights.
    - `--width` and `--height` are mutually exclusive within a single invocation.
    - Output dimensions must be exact for the specified axis (width or height), with the other axis computed to preserve aspect ratio.
  - **Skip upscaling:**
    - If a requested target size exceeds the original dimension in the chosen axis, that size must be skipped.
    - Skipped sizes must be logged with a clear reason (e.g., `Skipped 1200px: original is only 800px wide`).
    - Processing continues for remaining sizes.
  - **Input handling:**
    - Process a single image file per invocation.
    - Validate that the file exists and is readable; otherwise print `Error: File not found: <path>` and exit with a specific non-zero status.
    - Support absolute and relative paths, including paths with spaces and Unicode characters.
    - For the initial implementation, `resize` focuses on JPEG input; non-JPEG files must produce a clear unsupported format error.
  - **Output organization:**
    - Default output directory is `./resized/` relative to the current working directory.
    - Support `--output <directory>` to specify a custom output directory.
    - Create the output directory if it does not exist.
    - Preserve the original file extension and case.
    - Use a predictable naming pattern for outputs: `{basename}_{size}.{ext}` where `size` is the target dimension in pixels along the controlled axis.
  - **Quality control:**
    - Support a `--quality <1-100>` parameter controlling JPEG compression quality.
    - Default quality is 90.
    - Validate that quality is an integer between 1 and 100; invalid values must result in an error and non-zero exit.
  - **EXIF metadata handling for resized images:**
    - Strip EXIF metadata from resized outputs by default to optimize for web delivery.
    - Maintain color profile (ICC) information during conversion.
    - Future versions may add flags for preserving EXIF or stripping ICC profiles, but these are out of scope for the initial implementation.
  - **Format and codec behavior:**
    - Initial `resize` implementation targets JPEG input and JPEG output only.
    - Future versions may extend `resize` to work with additional input/output formats in coordination with `ipro convert`.

### 4.3 Image Conversion (`ipro convert`)

- **Requirement:** Convert images between Pillow-supported formats for web and social media workflows.
- **Primary Use Case:** Converting HEIC/HEIF images (from iPhone) to JPEG for web compatibility.
- **Acceptance Criteria:**
  - **Invocation:**
    - Support subcommand syntax: `ipro convert <source> --format <target_format> [options]`.
    - `<source>` is a required positional argument referring to the input image file.
    - `--format` is a required option specifying the desired output format (e.g., `jpeg`, `png`, `webp`).
  - **Format support:**
    - Accept any image format that Pillow can open as input (including HEIF/HEIC with `pillow-heif`).
    - Support JPEG, PNG, and WebP as output formats (v1.2+), with a clear path to extend to AVIF and others.
    - Provide meaningful errors for unsupported target formats.
  - **Output behavior:**
    - By default, create converted files in a `./converted/` directory (non-destructive).
    - Support `--output <directory>` to specify a custom output directory.
    - Use naming convention: `{basename}.{target_ext}` (e.g., `photo.heic` → `photo.jpg`).
    - If output file already exists, overwrite with warning message.
  - **EXIF metadata handling:**
    - **Default behavior:** Preserve EXIF metadata in converted output.
    - `--strip-exif` flag: Remove all EXIF metadata from output (useful for privacy or web optimization).
    - Note: Some target formats may not support all EXIF fields; preserve what is compatible.
  - **Quality control:**
    - Support `--quality <1-100>` for lossy formats (JPEG, WebP).
    - Default quality is 90.
  - **Relationship to resizing:**
    - `convert` focuses on format and encoding.
    - `resize` focuses on dimensions and quality.
    - Future versions may compose both behaviors (e.g., resize and convert in one step), but initial implementations treat them as separate commands.

### 4.4 File Renaming (`ipro rename`)

- **Requirement:** Rename image files based on actual file format or EXIF metadata for better organization.
- **Primary Use Cases:**
  - Fix mismatched file extensions (e.g., `.HEIC` files that are actually JPEG)
  - Add EXIF date prefixes for chronological sorting by filename
- **Acceptance Criteria:**
  - **Invocation:**
    - Support subcommand syntax: `ipro rename <file> [options]`.
    - `<file>` is a required positional argument referring to the image file.
    - At least one action flag is required: `--ext` or `--prefix-exif-date`.
  - **Extension correction (`--ext`):**
    - Read the actual image format from file content (not extension).
    - Create a copy with the corrected, lowercase extension.
    - Extension mapping: JPEG → `.jpg`, PNG → `.png`, HEIF → `.heic`, etc.
    - Lowercase is the default (internet-friendly for URLs).
    - Example: `photo.HEIC` (actually JPEG) → `photo.jpg`
    - Example: `image.HEIC` (actually HEIC) → `image.heic`
  - **EXIF date prefix (`--prefix-exif-date`):**
    - Extract `DateTimeOriginal` from EXIF metadata.
    - Prepend ISO-formatted date/time to filename.
    - Use format: `YYYY-MM-DDTHHMMSS_` (no colons, macOS-safe).
    - Example: `photo.jpg` → `2023-12-15T142305_photo.jpg`
    - If no EXIF date exists: skip file with warning message, exit successfully.
  - **Combined flags:**
    - `--ext` and `--prefix-exif-date` can be used together.
    - Both transformations applied to filename before creating the copy.
    - Example: `photo.HEIC` (JPEG, taken 2023-12-15 14:23:05) → `2023-12-15T142305_photo.jpg`
  - **Output behavior:**
    - **Default:** Create a copy with the new filename (non-destructive).
    - Output to same directory as source file by default.
    - Support `--output <directory>` for custom output location.
  - **Error handling:**
    - File not found → exit code 3.
    - Cannot read image format → exit code 4.
    - No EXIF date with `--prefix-exif-date` → warning, skip file, exit code 0.

### 4.5 Command-Line Interface

#### 4.5.1 Basic Syntax
```bash
ipro info <file> [options]
ipro resize <file> --width <sizes> [options]
ipro resize <file> --height <sizes> [options]
ipro convert <source> --format <target_format> [options]
ipro rename <file> --ext [options]
ipro rename <file> --prefix-exif-date [options]
```

#### 4.5.2 Required Parameters

- **`ipro info`**
  - `<file>`: path to source image file (positional, required).

- **`ipro resize`**
  - `--width <sizes>` **OR** `--height <sizes>` (mutually exclusive).
    - Comma-separated list of integers.
    - Example: `--width 300,600,900,1200`.
  - `<file>`: path to source image file (positional, required).

- **`ipro convert`**
  - `<source>`: path to source image file (positional, required).
  - `--format <target_format>`: desired output format (e.g., `jpeg`, `png`, `webp`).

- **`ipro rename`**
  - `<file>`: path to source image file (positional, required).
  - At least one of: `--ext` or `--prefix-exif-date`.

#### 4.5.3 Optional Parameters

- `--quality <1-100>` (default: 90) – for JPEG output (resize/convert).
- `--output <directory>` (default: `./resized/` for resize, `./converted/` for convert) – output directory.
- `--strip-exif` (convert, rename) – remove EXIF metadata from output.
- `--json` (info) – output metadata as JSON.
- `--short` (info) – output a single CSV line of key fields.
- `--csv` (info with field selection) – output comma-separated values.
- `--key-value` (info with field selection) – output key-value pairs.
- `-w` / `--width`, `-h` / `--height`, `--format`, `--aspect-ratio`, `--orientation` (info) – select specific fields.
- `--exif` / `--exif-all` (info) – include curated or full EXIF metadata.
- `--ext` (rename) – correct file extension based on actual format.
- `--prefix-exif-date` (rename) – prepend EXIF date to filename.
- `--help` / `-h` – display usage information.
- `--version` / `-v` – display version number.

#### 4.5.4 Usage Examples
```bash
# Inspect image information for a single file (human-readable)
ipro info photo.jpg

# Generate CSV of image metadata for all JPEGs in a directory
for img in *.jpg; do
  ipro info "$img" --short >> info.csv
done

# Basic usage - resize to multiple widths
ipro resize photo.jpg --width 300,600,900,1200

# Custom quality and output directory
ipro resize photo.jpg --width 300,600 --quality 85 --output ~/web/images/

# Resize by height instead of width
ipro resize banner.jpg --height 400,800

# Batch processing via shell loop for resizing
for img in *.jpg; do
  ipro resize "$img" --width 300,600,900
done

# Convert image to PNG
ipro convert photo.jpg --format png

# Convert and organize outputs in a specific directory
ipro convert photo.jpg --format webp --output ./converted/

# Convert HEIC to JPEG, stripping EXIF for privacy
ipro convert photo.heic --format jpeg --strip-exif

# Fix mismatched extension (e.g., .HEIC file that's actually JPEG)
ipro rename photo.HEIC --ext
# Result: photo.jpg (in same directory)

# Add EXIF date prefix for chronological sorting
ipro rename photo.jpg --prefix-exif-date
# Result: 2023-12-15T142305_photo.jpg

# Combine extension fix and date prefix
ipro rename photo.HEIC --ext --prefix-exif-date
# Result: 2023-12-15T142305_photo.jpg

# Get only specific fields from image info
ipro info photo.jpg --width --height
# Result: 1920 1080

ipro info photo.jpg -w -h --format --json
# Result: {"width": 1920, "height": 1080, "format": "JPEG", "filename": "photo.jpg"}

# Batch rename with extension fix
for img in *.HEIC; do
  ipro rename "$img" --ext || true
done
```

### 4.6 Error Handling

#### 4.6.1 Input Validation Errors
- **Common (all commands):**
  - Missing required parameters → exit with error message and usage hint.
  - Invalid file path → `Error: File not found: <path>`.
- **`ipro info` / `ipro convert`:**
  - Unsupported or unreadable image format → `Error: Unsupported or unreadable image format: <path>`.
- **`ipro resize`:**
  - Unsupported format (non-JPEG input) → `Error: Unsupported format. This version of resize supports JPEG only.`
  - Invalid quality value → `Error: Quality must be between 1-100`.
  - Both width and height specified → `Error: Cannot specify both --width and --height`.

#### 4.6.2 Processing Errors
- Corrupt image file → `Error: Cannot read image: <file>`.
- Permission denied → `Error: Cannot write to output directory: <path>`.
- Disk space issues → `Error: Insufficient disk space`.
- All sizes skipped (upscaling) in `resize` → warning, exit successfully with message.

#### 4.6.3 Error Behavior
- Exit with non-zero status code on errors.
- Print errors to stderr.
- Print normal output to stdout.
- Current design processes a single image per invocation; multi-file continuation semantics are out of scope for this version.

---

### 4.7 Output & Feedback

#### 4.7.1 Standard Output
- Summary of operations performed.
- For `resize` and `convert`: list of created files with dimensions and file sizes.
- For `info`: summary of image metadata (dimensions, orientation, aspect ratio, EXIF summary).
- Warnings for skipped sizes or other non-fatal issues.

#### 4.7.2 Example Output (Resize)
```
Processing: photo.jpg (2400x1600)
Output directory: ./resized/

✓ Created: photo_300.jpg (300x200, 45 KB)
✓ Created: photo_600.jpg (600x400, 128 KB)
✓ Created: photo_900.jpg (900x600, 256 KB)
✓ Created: photo_1200.jpg (1200x800, 412 KB)

Successfully created 4 images from photo.jpg
```

#### 4.7.3 Verbose Mode (Future)
- `--verbose` flag for detailed processing information.
- Show processing time per image.
- Display compression ratios.

#### 4.7.4 Quiet Mode (Future)
- `--quiet` flag to suppress all output except errors.
- Useful for scripting and automation.

---

## 5. Non-Functional Requirements

### 5.1 Performance
- Process a single 4000x3000 JPEG in < 5 seconds on modern hardware
- Memory usage should scale with image size (load one image at a time)
- No memory leaks during batch processing

### 5.2 Compatibility
- **Operating Systems:** macOS, Linux, Windows
- **Python Version:** Python 3.8+
- **Dependencies:** Pillow (PIL) library only

### 5.3 Reliability
- Graceful handling of corrupt images
- Atomic file writes (temp file + rename) to prevent partial outputs
- No data loss on interruption (Ctrl+C)

### 5.4 Usability
- Clear, actionable error messages
- Help text accessible via `--help`
- Follows Unix conventions (exit codes, stdin/stdout/stderr)

### 5.5 Maintainability
- Well-documented code with docstrings
- Unit tests for core functions
- Integration tests for CLI interface
- Semantic versioning

### 5.6 Testing & Test-Driven Development (TDD)
- **Test framework:** Use `pytest` as the primary test runner for unit, integration, and regression tests.
- **Unit tests:**
  - Cover core logic such as size parsing, JPEG validation, aspect ratio calculation, orientation classification, and EXIF extraction.
  - Verify behavior of helper functions used by `ipro info`, `ipro resize`, and `ipro convert`.
- **CLI integration tests:**
  - Invoke subcommands (`info`, `resize`, `convert`) via the command line within tests.
  - Assert on exit codes and key parts of stdout/stderr for success and error scenarios.
- **TDD workflow:**
  - For new features and significant changes, write failing tests first to capture the desired behavior.
  - Implement or modify code until tests pass, then refactor while keeping the test suite green.
  - Add regression tests for any reported bugs before fixing them.
- **Coverage expectations:**
  - Maintain high coverage (e.g., >80% of core modules) with particular focus on edge cases around file handling, EXIF metadata, and aspect ratio classification.

---

## 6. Technical Constraints

### 6.1 Dependencies
- **Pillow:** For image processing (resize, quality, format handling)
- **argparse:** For CLI argument parsing (Python stdlib)
- **pathlib:** For path handling (Python stdlib)

### 6.2 File System
- Must handle spaces and special characters in filenames
- Support Unicode filenames
- Work with relative and absolute paths

### 6.3 Image Processing
- Use Pillow's high-quality resampling (Lanczos filter)
- Maintain color accuracy during resize
- Handle both RGB and RGBA images appropriately

---

## 7. Future Enhancements (Post-V1.0)

### 7.1 Batch Processing (v1.1)
- Multiple input files
- Glob pattern support
- Directory recursion
- Progress bar for batch operations

### 7.2 Advanced Resizing (v1.2)
- Crop modes (center, smart, focal point)
- Fit modes (contain, cover, fill)
- Simultaneous width AND height with aspect ratio options

### 7.3 Format Support (v1.3)
- PNG input/output
- WebP support (modern web format)
- AVIF support (next-gen format)
- Format conversion capabilities

### 7.4 Metadata & Optimization (v1.4)
- Preserve EXIF option
- Progressive JPEG encoding
- Optimize PNG with pngquant
- Edit EXIF fields (copyright, author)

### 7.5 Responsive Web Features (v1.5)
- Generate HTML `<img>` tags with srcset
- Generate `<picture>` elements with multiple formats
- Output JSON manifest for static site generators
- Validate srcset size ordering

### 7.6 Configuration (v1.6)
- Config file support (`.imagerc`, `pyproject.toml`)
- Named presets (`--preset thumbnail`)
- Per-project configuration
- Environment variable support

### 7.7 Advanced Features (v2.0)
- Watermarking
- Image filters (grayscale, blur, sharpen)
- Smart cropping with face detection
- Parallel processing for batch operations
- Dry-run mode (`--dry-run`)

---

## 8. Success Metrics

### 8.1 Adoption Metrics
- GitHub stars and forks
- PyPI download count
- Community contributions

### 8.2 Quality Metrics
- Test coverage > 80%
- Zero critical bugs in production
- Average issue resolution time < 7 days

### 8.3 Performance Metrics
- Processing time per megapixel
- Memory usage benchmarks
- User-reported performance issues

---

## 9. Open Questions

1. **File Overwrite Behavior:** What should happen if output file already exists?
   - Overwrite silently?
   - Skip with warning?
   - Prompt user (breaks automation)?
   - Add `--force` flag?

2. **Dry-Run Mode:** Should v1.0 include `--dry-run` to preview operations?

3. **Progress Feedback:** For single-file mode, is progress output needed?

4. **Exit Codes:** Define specific exit codes for different error types?
   - 0 = success
   - 1 = general error
   - 2 = invalid arguments
   - 3 = file not found
   - 4 = processing error

5. **Color Output:** Should terminal output use colors (like the bash script)?
   - Requires colorama or similar library
   - Auto-detect TTY vs pipe

6. **Logging:** Should the tool support logging to file for debugging?

7. **Size Validation:** Should we validate that sizes are in ascending order for srcset?

---

## 10. Web Interface (Separate Section - TBD)

**Note:** Web interface requirements will be documented separately after CLI specification is finalized.

### Planned Features:
- Drag-and-drop file upload
- Visual configuration of resize parameters
- Real-time preview of resized images
- Batch processing with progress bar
- Download individual or zip all outputs
- Localhost web server (Flask/FastAPI)

**Status:** Requirements gathering in progress

---

## 11. Appendix

### 11.1 Related Tools
- ImageMagick (CLI tool, external dependency)
- sharp (Node.js library)
- Pillow (Python library - our foundation)
- libvips (high-performance C library)

### 11.2 References
- [Responsive Images - MDN](https://developer.mozilla.org/en-US/docs/Learn/HTML/Multimedia_and_embedding/Responsive_images)
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [11ty Image Plugin](https://www.11ty.dev/docs/plugins/image/)

### 11.3 Glossary
- **srcset:** HTML attribute for specifying multiple image sources at different resolutions
- **Aspect Ratio:** Proportional relationship between width and height
- **Upscaling:** Enlarging an image beyond its original dimensions
- **EXIF:** Metadata embedded in image files (camera settings, GPS, etc.)
- **Lanczos:** High-quality image resampling algorithm

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-12 | Initial | First draft based on requirements gathering |
| 1.2 | 2025-12-06 | Update | Added rename command (4.4), enhanced convert (4.3), info field selection, core non-destructive principle |

