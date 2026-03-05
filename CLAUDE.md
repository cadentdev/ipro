# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ipro is a Python CLI tool for responsive image processing, designed for web developers working with static site generators. It provides commands for inspecting image metadata, resizing, converting formats, and renaming based on EXIF data, with command chaining via `+`.

**Main file:** `ipro.py` (single-file Python script, ~1400 lines)
**Current version:** 1.3.0
**Python requirement:** 3.8+
**Primary dependency:** Pillow (PIL), pillow-heif (for HEIF/HEIC support)

## Development Commands

### Running the Tool
```bash
# Info command - inspect image metadata
python3 ipro.py info <file> [--json|--short] [--exif|--exif-all]

# Resize command - generate multiple image sizes
python3 ipro.py resize <file> --width <sizes> [--quality 90] [--output dir/]
python3 ipro.py resize <file> --height <sizes> [--quality 90] [--output dir/]

# Convert command - change image format
python3 ipro.py convert <file> --format jpeg [--quality 80] [--strip-exif]

# Rename command - rename based on format or EXIF date
python3 ipro.py rename <file> --ext [--prefix-exif-date] [--output dir/]

# Command chaining - pipe output between commands
python3 ipro.py convert photo.heic --format jpeg + resize --width 1080
python3 ipro.py resize photo.jpg --width 300,600 + convert --format webp
```

### Testing
```bash
# Run all tests (355 total)
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_info_cli.py -v
python -m pytest tests/test_security.py -v

# Run with coverage
python -m pytest tests/ --cov=ipro --cov-report=term-missing

# Run specific test
python -m pytest tests/test_info_cli.py::TestInfoCommandBasics::test_info_command_exists -v
```

### CI/CD
- GitHub Actions runs tests automatically on PRs
- Tests across Python 3.8, 3.9, 3.10, 3.11
- Workflow: `.github/workflows/test.yml`

## Architecture

### Single-File Design
All code lives in `ipro.py` - there are no separate modules. This keeps the tool simple and portable.

### Named Constants
Exit codes and defaults are defined as named constants near the top of the file:
- `EXIT_SUCCESS`, `EXIT_UNSUPPORTED_FORMAT`, `EXIT_INVALID_ARGS`, `EXIT_FILE_NOT_FOUND`, `EXIT_READ_ERROR`
- `DEFAULT_RESIZE_QUALITY` (90), `DEFAULT_CONVERT_QUALITY` (80), `DEFAULT_OUTPUT_DIR` ("output")
- `MAX_IMAGE_PIXELS` (100M), `MAX_INPUT_FILE_SIZE` (500MB), `MAX_SIZES_COUNT` (20)

### Subcommand Structure
The CLI uses argparse subparsers for command routing:
1. `_create_parser()` delegates to per-command parser functions:
   - `_add_info_parser(subparsers)` (line 1238)
   - `_add_resize_parser(subparsers)` (line 1253)
   - `_add_rename_parser(subparsers)` (line 1272)
   - `_add_convert_parser(subparsers)` (line 1288)
2. Each subcommand has a dedicated handler:
   - `cmd_info(args)` (line 927)
   - `cmd_resize(args)` (line 955)
   - `cmd_rename(args)` (line 1037)
   - `cmd_convert(args)` (line 1144)
3. Command chaining via `+` separator handled by `_execute_chain()` (line 1307)

### Key Helper Functions

**Shared helpers:**
- `validate_input_file(filepath)` - Validates file exists, checks size limit, warns on symlinks (line 213)
- `validate_output_path(output_str, input_path)` - Rejects path traversal, null bytes, warns on absolute paths (line 139)
- `resolve_output_dir(args_output, input_path)` - Output directory resolution with symlink check (line 183)
- `ensure_rgb_for_jpeg(img)` - Converts RGBA/LA/P to RGB with white background (line 112)

**Image information (`info` command):**
- `get_image_info(filepath)` - Main orchestrator for gathering all image metadata (line 680)
- `calculate_aspect_ratio(width, height)` - Computes reduced integer ratio using GCD (line 417)
- `classify_orientation(width, height)` - Returns "square", "landscape", or "portrait" (line 434)
- `match_common_ratio(ratio_str)` - Matches against common ratios (line 453)
- `extract_exif_data(filepath)` - Extracts EXIF metadata using Pillow (line 480)
- `format_exif_curated(exif_dict)` - Returns friendly subset of EXIF fields (line 509)
- `serialize_exif_value(value)` - Converts Pillow EXIF types to JSON-serializable types (line 824)
- `_format_info_json(info, args)` - JSON output formatter (line 846)
- `_format_info_csv(info)` - CSV output formatter (line 877)
- `_format_info_human(info, args)` - Human-readable output formatter (line 896)

**Image conversion (`convert` command):**
- `convert_image(...)` - Core conversion with sRGB, EXIF handling, GPS stripping (line 302)
- `convert_to_srgb(img)` - ICC profile conversion to sRGB (line 253)
- `_strip_gps_from_exif(exif_data)` - Removes GPS IFD for privacy (line 282)

**Image resizing (`resize` command):**
- `resize_image(input_path, output_dir, sizes, dimension, quality)` - Core resize logic (line 735)
- `parse_sizes(size_str)` - Parses comma-separated size list, enforces MAX_SIZES_COUNT (line 393)

**Image renaming (`rename` command):**
- `get_image_format(filepath)` - Content-based format detection (line 663)
- `format_exif_date_prefix(exif_date_str)` - EXIF date to filename prefix (line 581)
- `build_renamed_filename(original, ext, date_prefix)` - Construct new filename (line 629)

**Command chaining:**
- `split_chain(argv)` - Splits argv at `+` tokens into command segments (line 61)
- `_execute_chain(segments)` - Runs chained commands, piping output paths between them (line 1307)

### Exit Code Convention
Defined as named constants:
- `EXIT_SUCCESS` (0) - Success
- `EXIT_UNSUPPORTED_FORMAT` (1) - Unsupported format or unreadable image
- `EXIT_INVALID_ARGS` (2) - Invalid arguments
- `EXIT_FILE_NOT_FOUND` (3) - File not found
- `EXIT_READ_ERROR` (4) - Cannot read/process image

### Security Features
Added in the refactor-and-harden pass:
- **Path traversal protection:** `--output` rejects `..` components and null bytes
- **Decompression bomb limit:** 100 megapixel cap via `Image.MAX_IMAGE_PIXELS`
- **File size limit:** 500MB input file cap
- **Symlink detection:** Warns on symlink inputs, rejects symlink output directories
- **Resize count limit:** Maximum 20 sizes per invocation
- **GPS stripping:** GPS metadata stripped by default when EXIF is preserved in convert
- **Overwrite warnings:** Rename warns when output file exists
- **Chain integrity:** Verifies intermediate files exist between chained commands
- **Secure temp files:** Uses `tempfile.mkstemp()` for case-insensitive rename operations

## Test-Driven Development (TDD)

This project follows strict TDD practices:

### Test Organization
```
tests/
├── conftest.py             # Pytest configuration
├── fixtures.py             # Test image generation with synthetic EXIF
├── test_info_helpers.py    # Unit tests for info helper functions
├── test_info_cli.py        # CLI integration tests for info
├── test_resize_helpers.py  # Unit tests for resize helpers
├── test_resize_cli.py      # CLI integration tests for resize
├── test_convert_helpers.py # Unit tests for convert helpers
├── test_convert_cli.py     # CLI integration tests for convert
├── test_rename_helpers.py  # Unit tests for rename helpers
├── test_rename_cli.py      # CLI integration tests for rename
├── test_chain_helpers.py   # Unit tests for chain helpers
├── test_chain_cli.py       # CLI integration tests for chaining
├── test_cli_direct.py      # Direct CLI invocation tests
└── test_security.py        # Security-focused tests (25 tests)
```

### TDD Workflow for New Features
1. **Write tests first** - Define expected behavior through tests before implementation
2. **Run tests and watch them fail** - Confirm tests fail as expected (red)
3. **Implement minimal code** - Write just enough to make tests pass (green)
4. **Refactor** - Improve code while keeping tests green
5. **Maintain coverage** - Aim for >80% on core logic

### Test Coverage
- **Info command:** 100% coverage
- **Resize command:** ~95% coverage
- **Convert command:** 100% coverage
- **Rename command:** 100% coverage
- **Command chaining:** 100% coverage
- **Security tests:** 25 tests covering path traversal, symlinks, decompression bombs, size limits, GPS stripping
- **Overall:** 355 total tests

## PRD and Task Tracking

**Critical:** Always reference `PRD.md` (Product Requirements Document) for feature specifications and requirements. It is the source of truth for expected behavior.

**Task tracking:** `TASKS.md` tracks implementation progress against the PRD. Check it to understand what's done and what's planned.

## File Naming Convention

Resized images use pattern: `{basename}_{size}.{ext}`
- `photo.jpg` resized to 300px → `photo_300.jpg`
- Size suffix represents the controlled dimension (width or height)

## Image Processing Details

### Resize Behavior
- **Algorithm:** Lanczos resampling (high-quality)
- **Aspect ratio:** Always preserved
- **Upscaling:** Automatically prevented with warnings
- **EXIF:** Stripped by default from resized outputs
- **Transparency:** Converted to white background for JPEG via `ensure_rgb_for_jpeg()`
- **Color mode:** Converts to RGB for JPEG output
- **Format validation:** Content-based via `get_image_format()` (not extension-based)
- **Size limit:** Maximum 20 sizes per invocation

### Convert Behavior
- **sRGB conversion:** Automatic, converts from any ICC profile to sRGB
- **EXIF handling:** Preserved by default. GPS data stripped by default for privacy.
- **Formats:** JPEG, PNG, WebP
- **Quality range:** 1-100 (default: 80)
- **`--strip-exif`:** Removes all EXIF metadata

### Rename Behavior
- **Non-destructive:** Creates a copy, never modifies the original
- **`--ext`:** Corrects extension based on actual image format (content-based detection)
- **`--prefix-exif-date`:** Prepends EXIF date as `YYYY-MM-DDTHHMMSS_`
- **Case-insensitive safety:** Uses secure temp files for case-only renames

### Info Command Specifics
- **EXIF orientation:** Automatically handled by Pillow
- **Aspect ratios:** Exact integer matching only (uses GCD for reduction)
- **Common ratios:** 1:1, 4:3, 3:2, 16:9, 5:4, 4:5, 9:16, 1.91:1 (as 191:100)
- **Format support:** Any Pillow-compatible format (JPEG, PNG, HEIF, etc.)

### Output Directory
- Default: `output/` next to source file, created if doesn't exist
- If input is already in `output/`, reuses it (for chaining)
- `--output` flag: validates against path traversal (`..`, null bytes, symlinks)

## Important Patterns

### Error Handling
- Print errors to `stderr`, normal output to `stdout`
- Use descriptive error messages with context
- Exit with named constant status codes
- Helper functions raise exceptions; only `cmd_*` handlers call `sys.exit()`
- Specific exception types used where possible (e.g., `PyCMSError` for ICC profile errors)
- Partial output files cleaned up on conversion failure

### Output Formatting
The `info` command supports three output modes via dedicated formatter functions:
- **Default:** Human-readable multi-line via `_format_info_human()` (for terminal use)
- **`--json`:** Single JSON object via `_format_info_json()` (JSONL-compatible)
- **`--short`:** Single CSV line via `_format_info_csv()` (for batch processing)

## Dependencies

Keep dependencies minimal:
- **Pillow (>=10.0.0):** Core image processing library
- **pillow-heif (>=0.13.0):** HEIF/HEIC format support (enables iPhone photo formats)
- **pytest (>=7.0.0):** Testing framework

**Note:** The `pillow-heif` dependency is automatically registered on import with graceful fallback if unavailable. See lines 20-24 in `ipro.py`.

Avoid adding new dependencies unless absolutely necessary.

## Format Support

**All Commands (Read):**
- JPEG, PNG, HEIF/HEIC (requires pillow-heif), DNG (RAW), BMP, GIF, TIFF, WebP
- Format detection based on file content, not extension (via `get_image_format()`)

**Convert Command (Write):**
- JPEG, PNG, WebP

**Resize Command:**
- Content-validated input (any Pillow-readable format)
- JPEG output
