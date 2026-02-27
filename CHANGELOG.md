# Changelog

All notable changes to ImgPro will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Custom field selection for `imgpro info` command
- AVIF output format support
- `--no-srgb` flag for convert command
- `--verbose` and `--quiet` modes

---

## [1.4.0] - 2026-02-27

### Added
- **First-class MPO format support** (fixes #17):
  - MPO files recognized as distinct format (not silently treated as JPEG)
  - `info` command shows `Format: MPO` and `Frames: N` for multi-frame images
  - `resize` command accepts MPO files alongside JPEG
  - `convert` command warns about dropped frames and suggests `extract`
  - `rename --ext` maps MPO to `.jpg` extension (correct output format)
  - JSON and CSV output include `format` and `frames` fields
- **`extract` subcommand** for multi-frame images (closes #18):
  - Exports individual frames from MPO, animated GIF, APNG, WebP, and TIFF
  - Output naming: `{basename}_{NNN}.{ext}` with zero-padded numbering
  - Chainable with other commands via `+` (e.g., `extract + resize --width 400`)
  - Symlink protection on output paths
  - Informational note when extracting from single-frame images

### Changed
- `info --short` (CSV) field order updated: format and frames fields added at positions 2-3
- Updated version to 1.4.0

---

## [1.3.1] - 2026-02-12

### Changed
- **Refactored** codebase for improved maintainability:
  - Named constants for all exit codes, quality defaults, and output directory name
  - All imports moved to module top level
  - Context managers on all `Image.open()` calls (fixed 3 resource leaks)
  - `sys.exit()` removed from helper functions (raise exceptions instead)
  - Shared helpers extracted: `resolve_output_dir()`, `validate_input_file()`, `ensure_rgb_for_jpeg()`
  - `validate_jpeg()` (extension-only) eliminated in favor of content-based `get_image_format()`
  - Parser construction modularized into per-command functions
  - `cmd_info` output formatters extracted into dedicated functions
- **Security hardening** (13 findings from adversarial red-team review):
  - Path traversal protection on `--output` flag (rejects `..` components and null bytes)
  - Decompression bomb limit: 100 megapixel cap + 500MB file size cap
  - Symlink detection on input (warn) and output directories (reject)
  - Resize size count capped at 20
  - Overwrite warning in rename command
  - Bare `except:` replaced with `except Exception:` in `serialize_exif_value()`
  - Specific `PyCMSError` catch in `convert_to_srgb()`
  - Partial output file cleanup on conversion failure
  - Chain integrity verification for intermediate files
  - GPS metadata stripped by default when EXIF is preserved in convert
  - Secure temp files via `tempfile.mkstemp()` in case-insensitive rename
  - ASCII-only validation for EXIF date prefix digits

### Added
- `tests/test_security.py` - 25 security-focused tests covering path traversal, decompression bombs, symlinks, size limits, GPS stripping, and more

---

## [1.3.0] - 2026-02-12

### Added
- **Command chaining** with `+` separator: output of each command feeds into the next
  - `imgpro convert photo.heic --format jpeg + resize --width 1080`
  - Multi-file fan-out: resize with multiple widths chains each output individually
- **Source-relative output directory**: default `output/` is created next to the source file, not CWD
  - Chained commands reuse the output directory when input is already in `output/`

### Changed
- Updated version to 1.3.0
- Documentation updated for command chaining and source-relative output

---

## [1.2.1] - 2026-01-12

### Changed
- **BREAKING**: Resize command now uses positional `<file>` argument instead of `--input` flag
  - Before: `imgpro resize --input photo.jpg --width 300`
  - After: `imgpro resize photo.jpg --width 300`
  - Aligns resize command with other commands (info, rename, convert) per PRD specification

### Added
- `scripts/prepare-instagram.sh` - Automated workflow for Instagram image preparation (convert, resize, organize)
- `scripts/README.md` - Comprehensive documentation for batch processing scripts
- `DONE.md` - Archive file for completed development tasks

### Fixed
- Renamed project from `imagepro` to `imgpro` for consistency

### Documentation
- Updated README with improved formatting and consistency
- Updated all resize command examples to use positional file argument
- Cleaned up CLAUDE.md and removed outdated CLI discrepancy section
- Reorganized task tracking (TASKS.md cleaned up, completed tasks moved to DONE.md)

---

## [1.2.0] - 2025-12-06

### Added
- **WebP output format support** for `imgpro convert` command
- **Batch processing scripts** in `scripts/` directory:
  - `rename-all.sh` - Add EXIF date prefix and correct extensions
  - `convert-all.sh` - Convert images to JPEG with sRGB profile
  - `resize-all.sh` - Resize images to specified width(s)
  - `organize-by-orientation.sh` - Organize by orientation or aspect ratio
- `scripts/README.md` with comprehensive usage examples
- sRGB color profile conversion (automatic) for convert command
- EXIF preservation by default in convert command
- `--strip-exif` flag for convert command

### Fixed
- Case-insensitive filesystem handling for rename command (macOS/Windows)

### Changed
- Default JPEG quality changed from 90 to 80 for convert command
- Updated documentation (README, TASKS, PRD) to reflect v1.2.0 features

---

## [1.1.0] - 2025-12-06

### Added
- HEIF/HEIC format support via `pillow-heif` package
- Comprehensive documentation updates (README, PRD, TASKS, CLAUDE.md)
- Test coverage improvements toward 100%
- Bash error handling patterns documented in README

### Changed
- Updated version to 1.1.0
- Improved test fixtures with synthetic EXIF data

---

## [1.0.0] - 2025-11-12

### Added
- Initial release of ImgPro CLI tool
- `imgpro info` subcommand for image metadata inspection
  - Pixel dimensions with EXIF orientation handling
  - Orientation classification (portrait, landscape, square)
  - Aspect ratio calculation using GCD
  - Common ratio matching (1:1, 4:3, 3:2, 16:9, 5:4, 4:5, 9:16, 1.91:1)
  - File metadata (name, path, size in KB)
  - EXIF extraction with curated subset (date taken, camera make/model, DPI)
  - Three output formats: default (human-readable), `--json`, `--short` (CSV)
  - `--exif` and `--exif-all` flags for EXIF data display
- `imgpro resize` subcommand for responsive image generation
  - Width-based resizing with `--width` option
  - Height-based resizing with `--height` option
  - Aspect ratio preservation
  - Upscaling prevention with warnings
  - JPEG quality control (1-100, default: 90)
  - Custom output directory with `--output`
  - Automatic output directory creation
  - EXIF stripping for web-optimized output
  - Lanczos resampling for high-quality results
- Comprehensive test suite (124 tests)
  - Unit tests for helper functions
  - CLI integration tests
  - Synthetic EXIF test fixtures
- GitHub Actions CI/CD pipeline
  - Automated testing on PRs
  - Multi-version Python support (3.8, 3.9, 3.10, 3.11)
- Error handling with specific exit codes
  - 0: Success
  - 1: Unsupported/unreadable format
  - 2: Invalid arguments
  - 3: File not found
  - 4: Cannot read/process image

### Technical Details
- Single-file architecture (`imgpro.py`)
- Python 3.8+ requirement
- Pillow dependency for image processing
- argparse subcommand pattern for CLI routing

---

## Document History

| Version | Date | Description |
|---------|------|-------------|
| 1.4.0 | 2026-02-27 | First-class MPO format support, extract subcommand for multi-frame images |
| 1.3.1 | 2026-02-12 | Refactoring and security hardening (13 findings fixed, 25 security tests) |
| 1.3.0 | 2026-02-12 | Command chaining with `+`, source-relative output directory |
| 1.2.1 | 2026-01-12 | Breaking: resize uses positional file arg, Instagram script, project rename |
| 1.2.0 | 2025-12-06 | WebP support, batch scripts, sRGB conversion |
| 1.1.0 | 2025-12-06 | Added HEIF/HEIC support, rename/convert commands |
| 1.0.0 | 2025-11-12 | Initial release with info and resize commands |
