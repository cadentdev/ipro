# ipro Completed Tasks

This document archives completed implementation tasks from `TASKS.md`.

---

## ✅ Completed Tasks

### 1. Implement `ipro info` (Section 4.1 of PRD)

**Status:** Completed via PR #3
**Test Coverage:** 69/69 tests passing (36 unit + 33 CLI integration)

- [x] Core CLI wiring
  - [x] Add an `info` subcommand to `ipro.py`
  - [x] Use positional `<file>` argument: `ipro info <file> [options]`
  - [x] Add flags: `--json`, `--short`, `--exif`, `--exif-all`

- [x] Core behavior
  - [x] Open file with Pillow; fail cleanly if unreadable or unsupported
  - [x] Read pixel dimensions, taking EXIF orientation into account
  - [x] Classify orientation: `portrait`, `landscape`, `square`
  - [x] Compute reduced integer aspect ratio (`ratio_raw`) using GCD
  - [x] Match `ratio_raw` against common ratios (1:1, 4:3, 3:2, 16:9, 5:4, 4:5, 9:16, 1.91:1)
  - [x] Report `common_ratio` or `none`

- [x] File and EXIF metadata
  - [x] Report filename, path, file size in KB
  - [x] Detect presence of EXIF
  - [x] Extract curated EXIF subset (date taken, make, model, orientation, DPI)
  - [x] Add `--exif-all` support to dump all EXIF tags

- [x] Output formats
  - [x] Default: human-readable multi-line summary
  - [x] `--json`: one JSON object per invocation (JSONL-friendly)
  - [x] `--short`: one CSV line per invocation with fixed column order

- [x] Error handling & exit codes
  - [x] Use exit code scheme (0=success, 3=not found, 1=error, 2=invalid args)
  - [x] Ensure errors go to stderr; normal output goes to stdout

### 2. Testing & TDD Setup (Section 5.6)

- [x] Add pytest to the project
  - [x] Add `pytest` to `requirements.txt`
  - [x] Create `tests/` directory structure
  - [x] Set up test fixtures with synthetic EXIF data

- [x] Unit tests for `info` helpers (36 tests)
  - [x] Aspect ratio calculation and common ratio matching
  - [x] Orientation classification
  - [x] EXIF extraction logic

- [x] CLI integration tests for `info` (33 tests)
  - [x] Success and error paths
  - [x] Test `--json`, `--short`, `--exif`, `--exif-all` flags
  - [x] Assert on exit codes and stderr/stdout separation

- [x] Unit tests for `resize` helpers (28 tests)
  - [x] Test `parse_sizes`, `validate_jpeg`, `get_file_size_kb`
  - [x] Test resize_image function with various dimensions
  - [x] Test upscaling prevention and aspect ratio preservation
  - [x] Test quality settings and output directory creation

- [x] CLI integration tests for `resize` (27 tests)
  - [x] Success and error paths
  - [x] Width/height mutual exclusion
  - [x] Quality validation and output directory creation
  - [x] Upscaling prevention and output format

- [x] CI/CD Setup
  - [x] GitHub Actions workflow for automated testing on PRs
  - [x] Tests across Python 3.8, 3.9, 3.10, 3.11

### 3. Implement `ipro rename` (Section 4.4 of PRD)

**Status:** Completed in v1.1.0

The `rename` command provides two key features for organizing image files:

1. Fix mismatched extensions based on actual file format
2. Prepend EXIF date/time for chronological sorting

- [x] Write tests first (TDD)
  - [x] Unit tests for format detection and extension mapping
  - [x] Unit tests for EXIF date extraction and formatting
  - [x] Unit tests for filename transformation logic
  - [x] CLI integration tests for `--ext` flag
  - [x] CLI integration tests for `--prefix-exif-date` flag
  - [x] CLI integration tests for combined flags
  - [x] Tests for missing EXIF date (skip with warning)
  - [x] Tests for output directory option

- [x] Implement `rename` command
  - [x] Add `rename` subparser with positional `<file>` argument
  - [x] Implement `--ext` flag for extension correction
    - [x] Read actual image format from file content
    - [x] Map format to lowercase extension (JPEG→.jpg, PNG→.png, HEIF→.heic)
    - [x] Create copy with corrected extension
  - [x] Implement `--prefix-exif-date` flag
    - [x] Extract DateTimeOriginal from EXIF
    - [x] Format as YYYY-MM-DDTHHMMSS_ (no colons for macOS)
    - [x] Skip file with warning if no EXIF date
  - [x] Support `--output <directory>` option
  - [x] Exit codes: 0=success, 3=not found, 4=cannot read

### 4. Implement `ipro convert` (Section 4.3 of PRD)

**Status:** Completed in v1.2.0

The `convert` command enables format conversion, primarily HEIC→JPEG.

- [x] Core implementation complete
  - [x] Add `convert` subparser with positional `<source>` argument
  - [x] Implement `--format` option (required: jpeg, png, webp)
  - [x] Default output to `./converted/` directory
  - [x] Preserve EXIF by default
  - [x] Implement `--strip-exif` flag to remove metadata
  - [x] Support `--quality` option (default: 80)
  - [x] Handle existing output files (overwrite with warning)
  - [x] sRGB color profile conversion (automatic)
  - [x] WebP output format support

- [x] Tests complete (50+ tests)
  - [x] CLI integration tests for basic conversion
  - [x] CLI integration tests for `--strip-exif` flag
  - [x] CLI integration tests for `--quality` option
  - [x] Tests for output directory and naming
  - [x] Tests for WebP conversion

### 5. Create Bash Scripts in `scripts/` Directory

**Status:** Completed in v1.2.0

Utility scripts demonstrating batch workflows with ipro.

- [x] Create `scripts/` directory structure
- [x] Create `scripts/README.md` with usage examples

- [x] Script 1: `resize-all.sh`
  - [x] Resize all images in directory to specified width
  - [x] Skip files already smaller than target width
  - [x] Use `python3 ipro.py` invocation

- [x] Script 2: `organize-by-orientation.sh`
  - [x] Copy images to subdirectories by orientation (landscape/, portrait/, square/)
  - [x] Variant: organize by aspect ratio (4x3/, 3x4/, 16x9/, etc.)
  - [x] Handle directory naming without colons

- [x] Script 3: `rename-all.sh`
  - [x] Add EXIF date prefix to filenames
  - [x] Correct file extensions based on actual format

- [x] Script 4: `convert-all.sh`
  - [x] Convert all images to JPEG with sRGB profile
  - [x] Configurable quality via environment variable
  - [x] Force mode to re-convert existing JPEGs
