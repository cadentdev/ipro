# ipro Task List

This document tracks implementation progress based on `PRD.md`.

**Last Updated:** 2026-01-07

---

## 📋 In Progress / Planned

### 6. Align `ipro resize` with PRD (Section 4.2) - Completed

> **Status:** Completed via PR #12 (2026-01-07)
> **Breaking Change:** Removed `--input` flag in favor of positional `<file>` argument.

- [x] Refactor CLI to match PRD
  - [x] Introduce positional `<file>` for `resize`
  - [x] Breaking change: removed `--input` flag (not backwards compatible)
  - [x] Help text now matches PRD style

- [x] Update documentation
  - [x] Update `README.md` examples to use positional `<file>`
  - [x] Update CLAUDE.md examples to use positional `<file>`

### 7. Enhanced `ipro info` Field Selection (Section 4.1 of PRD) - Priority 4

> **Status:** Not started
> **Depends on:** None

Add individual field flags for selective metadata output.

- [ ] Write tests first (TDD)
  - [ ] Tests for individual field flags (-w, -h, --format, etc.)
  - [ ] Tests for multiple field combination
  - [ ] Tests for output formats (space-separated, --csv, --json, --key-value)
  - [ ] Tests for JSON always including filename

- [ ] Implement field selection
  - [ ] Add `-w`/`--width` flag
  - [ ] Add `-h`/`--height` flag (note: conflicts with --help, may need adjustment)
  - [ ] Add `--format` flag
  - [ ] Add `--aspect-ratio` flag
  - [ ] Add `--orientation` flag
  - [ ] Implement space-separated output (default)
  - [ ] Implement `--csv` output format
  - [ ] Implement `--key-value` output format
  - [ ] Ensure `--json` includes filename

---

## 🎯 Future Enhancements

### Nice-to-Haves (PRD Section 7.x)

- [ ] Add `--verbose` and `--quiet` modes (PRD 4.6.3–4.6.4)
  - [ ] Implement verbose mode with detailed processing info
  - [ ] Implement quiet mode (errors only)
  - [ ] Add tests for both modes

- [ ] Explore batch-oriented UX (PRD 7.1)
  - [ ] Design multi-file input interface
  - [ ] Add progress bar for batch operations
  - [ ] Consider glob pattern support

- [ ] Add image format detection to `info` command
  - [ ] Detect actual image format from file content (not just extension)
  - [ ] Report format via Pillow's `Image.format` attribute
  - [ ] Add to default, JSON, and CSV outputs
  - [ ] Distinguish between file extension and actual format (e.g., .HEIC file containing JPEG data)

- [ ] Additional EXIF features
  - [ ] Revisit DPI reporting for IG workflows
  - [ ] Add more EXIF fields based on user feedback
  - [ ] EXIF editing capabilities

- [ ] Advanced resizing features (PRD 7.2)
  - [ ] Crop modes (center, smart, focal point)
  - [ ] Fit modes (contain, cover, fill)

- [ ] Format expansion (PRD 7.3)
  - [ ] WebP support
  - [ ] AVIF support
  - [ ] Additional format conversions

- [ ] Script: `generate-responsive-set.sh` (lower priority)
  - [ ] Create multiple width versions for srcset
  - [ ] Output organized for HTML integration

- [ ] Convert command enhancements
  - [ ] Add `--no-srgb` flag to skip sRGB conversion

---

## 📊 Project Status

**Current Version:** 1.3.1
**Test Coverage:** 355 tests (330 functional + 25 security)

- Info command: 100%
- Resize command: ~95%
- Convert command: 100%
- Rename command: 100%
- Command chaining: 100%
- Security: 25 tests (path traversal, symlinks, decompression bombs, size limits, GPS stripping)

**Next Priorities (in order):**

1. Add field selection to `ipro info` command
2. Add `--verbose` and `--quiet` modes

**Core Principle:** All file-modifying commands create copies by default (non-destructive).

**See also:** `DONE.md` for completed tasks archive.
