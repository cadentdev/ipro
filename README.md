# ipro

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/cadentdev/ipro/actions/workflows/test.yml/badge.svg)](https://github.com/cadentdev/ipro/actions/workflows/test.yml)
[![Code Style](https://img.shields.io/badge/code%20style-PEP8-brightgreen.svg)](https://www.python.org/dev/peps/pep-0008/)

Cross-platform image processing tools written in Python.

A command-line tool for generating multiple resolutions of images to support responsive web design workflows, specifically for static site generators like 11ty. ipro enables developers to create `srcset`-ready images from source files with configurable dimensions and quality settings.

## Features

### Info Command (v1.0)

- **Image Metadata Inspection**: View dimensions, orientation, aspect ratio, and file size
- **EXIF Support**: Extract and display EXIF metadata (camera, date, DPI, etc.)
- **Multiple Output Formats**: Human-readable, JSON, or CSV for batch processing
- **Common Aspect Ratios**: Automatic detection of standard ratios (16:9, 4:3, 1:1, Instagram 1.91:1, etc.)
- **Broad Format Support**: JPEG, PNG, HEIF/HEIC, DNG (RAW), BMP, GIF, TIFF, WebP, and other Pillow-compatible formats

### Resize Command (v1.0)

- **Multiple Resolutions**: Generate multiple image sizes from a single source
- **Width/Height Based**: Resize by width or height while maintaining aspect ratio
- **Smart Upscaling Prevention**: Automatically skips sizes larger than the original
- **High-Quality Resampling**: Uses Lanczos algorithm for best quality
- **JPEG Optimization**: Control quality (1-100) with EXIF stripping by default
- **Organized Output**: Configurable output directory with clean naming (`photo_300.jpg`)
- **Format Support**: JPEG only in v1.0 (PNG, WebP, AVIF planned for future versions)

### Convert Command (v1.1+)

- **Format Conversion**: Convert between JPEG, PNG, and WebP formats
- **HEIC/HEIF Support**: Convert iPhone photos to web-compatible formats
- **sRGB Color Profile**: Automatic conversion to sRGB for consistent web display
- **Quality Control**: Configurable quality for lossy formats (default: 80)
- **EXIF Handling**: Preserve or strip metadata with `--strip-exif` flag
- **MPO Support**: Handle multi-picture object files from cameras

### Rename Command (v1.1+)

- **EXIF Date Prefix**: Add `YYYY-MM-DDTHHMMSS_` prefix for chronological sorting
- **Extension Correction**: Fix mismatched extensions based on actual file format
- **Non-Destructive**: Creates copies, preserving originals

## Installation

### Install from PyPI (recommended)

```bash
# With pipx (isolated environment, adds to PATH)
pipx install ipro-cli

# Or with pip
pip install ipro-cli
```

Then run from anywhere:

```bash
ipro --help
```

To uninstall:

```bash
pipx uninstall ipro-cli
# or: pip uninstall ipro-cli
```

### Install from source

For development or to get the latest unreleased changes:

```bash
git clone https://github.com/cadentdev/ipro.git
cd ipro
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt

# Or install with pipx from the local clone
pipx install .
```

### Troubleshooting Installation

**`python3 -m venv` fails** (common in minimal containers, Docker, Proxmox LXC):

```bash
# If you see: "ensurepip is not available"
# Option 1: Install the venv package (requires sudo)
sudo apt install python3.12-venv  # adjust version as needed

# Option 2: Install without venv (no sudo required)
curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
python3 /tmp/get-pip.py --user --break-system-packages
python3 -m pip install --user --break-system-packages pillow pillow-heif pytest
```

**`pip3: command not found`**: Bootstrap pip first using Option 2 above.

### Dependencies

- **Pillow** (>=10.0.0): Python Imaging Library for image processing
- **pillow-heif** (>=0.13.0): HEIF/HEIC format support (enables reading iPhone photos in HEIC format)
- **pytest** (>=7.0.0): Testing framework (for development)

## Usage

ipro provides several commands for image processing workflows.

### Basic Syntax

```bash
# Info command - inspect image metadata
python3 ipro.py info <file> [options]

# Resize command - generate multiple sizes
python3 ipro.py resize <file> --width <sizes> [options]
python3 ipro.py resize <file> --height <sizes> [options]

# Convert command - change image format
python3 ipro.py convert <file> --format <format> [options]

# Rename command - fix extensions and add date prefix
python3 ipro.py rename <file> --ext --prefix-exif-date [options]
```

---

## Info Command

Inspect image files to view dimensions, orientation, aspect ratio, and EXIF metadata.

### Info Command Usage

```bash
python3 ipro.py info <file> [options]
```

### Info Parameters

**Required:**

- `<file>`: Path to image file

**Supported Formats:**

- **Common formats**: JPEG (.jpg, .jpeg), PNG (.png)
- **Apple formats**: HEIF/HEIC (.heic) - requires pillow-heif
- **RAW formats**: DNG (.dng) - Adobe Digital Negative
- **Other formats**: BMP, GIF, TIFF, WebP, and all Pillow-compatible formats

**Optional:**

- `--json`: Output as JSON (JSONL-compatible)
- `--short`: Output as CSV line (for batch processing)
- `--exif`: Display curated EXIF metadata
- `--exif-all`: Display all EXIF tags

### Info Examples

#### Basic Image Info

```bash
python3 ipro.py info photo.jpg
```

**Output:**

```text
File: photo.jpg
Path: /home/user/photos/photo.jpg
Dimensions: 1920x1080
Orientation: landscape
Aspect Ratio: 16:9 (16:9)
File Size: 245.32 KB
EXIF Present: Yes
```

#### JSON Output

```bash
python3 ipro.py info photo.jpg --json
```

**Output:**

```json
{"filename": "photo.jpg", "path": "/home/user/photos/photo.jpg", "width": 1920, "height": 1080, "orientation": "landscape", "ratio_raw": "16:9", "common_ratio": "16:9", "size_kb": 245.32, "has_exif": true, "creation_date": "2024:11:12 14:30:00", "exif": {"date_taken": "2024:11:12 14:30:00", "camera_make": "Canon", "camera_model": "Canon EOS 5D"}}
```

#### CSV Output for Batch Processing

```bash
# Generate CSV of all images in a directory (multiple formats)
for img in *.{jpg,jpeg,JPG,JPEG,png,heic,HEIC}; do
  python3 ipro.py info "$img" --short 2>/dev/null >> images.csv || true
done
```

**Note:** The `2>/dev/null || true` pattern makes the loop continue even if some files can't be read, which is useful when processing mixed file types.

**Output (images.csv):**

```text
photo1.jpg,1920,1080,landscape,16:9,16:9,245.32,2024:11:12 14:30:00
photo2.jpg,1080,1920,portrait,9:16,9:16,189.45,2024:11:12 15:00:00
photo3.jpg,1000,1000,square,1:1,1:1,156.78,
```

#### View EXIF Metadata

```bash
python3 ipro.py info photo.jpg --exif
```

**Additional output:**

```text
EXIF Data:
  Date Taken: 2024:11:12 14:30:00
  Camera Make: Canon
  Camera Model: Canon EOS 5D Mark IV
  Orientation: 1
  Dpi X: 72.0
  Dpi Y: 72.0
```

---

## Resize Command

Generate multiple image sizes from a single source while maintaining aspect ratio.

### Resize Command Usage

```bash
python3 ipro.py resize <file> --width <sizes> [options]
python3 ipro.py resize <file> --height <sizes> [options]
```

### Resize Parameters

**Required:**

- `<file>`: Path to source image file (JPEG only in v1.0)
- `--width <sizes>` OR `--height <sizes>` (mutually exclusive)
  - Comma-separated list of integers
  - Example: `--width 300,600,900,1200`

**Optional:**

- `--quality <1-100>` (default: 90)
  - JPEG compression quality
- `--output <directory>` (default: `output/` next to source file)
  - Directory for output images
- `--help` / `-h`
  - Display usage information
- `--version` / `-v`
  - Display version number

### Resize Examples

#### Resize to Multiple Widths

```bash
python3 ipro.py resize photo.jpg --width 300,600,900,1200
```

**Output:**

```text
Processing: photo.jpg (2400x1600)
Output directory: ./resized/

✓ Created: photo_300.jpg (300x200, 45 KB)
✓ Created: photo_600.jpg (600x400, 128 KB)
✓ Created: photo_900.jpg (900x600, 256 KB)
✓ Created: photo_1200.jpg (1200x800, 412 KB)

Successfully created 4 image(s) from photo.jpg
```

#### Custom Quality and Output Directory

```bash
python3 ipro.py resize photo.jpg --width 300,600 --quality 85 --output ~/web/images/
```

#### Resize by Height

```bash
python3 ipro.py resize banner.jpg --height 400,800
```

#### Batch Processing with Shell Loop

```bash
# Using ipro in PATH (see "Add to PATH" section)
for img in *.jpg; do
  ipro resize "$img" --width 1080 --quality 80
done

# Or using python3 directly
for img in *.jpg; do
  python3 ipro.py resize "$img" --width 300,600,900
done
```

#### Process with Find Command

```bash
find ./photos -name "*.jpg" | while read img; do
  python3 ipro.py resize "$img" --width 300,600 --output ./resized/
done
```

---

## Convert Command

Convert images between formats with automatic sRGB color profile conversion.

### Convert Command Usage

```bash
python3 ipro.py convert <file> --format <format> [options]
```

### Convert Parameters

**Required:**

- `<file>`: Path to source image file
- `--format <format>`: Target format (`jpeg`, `jpg`, `png`, `webp`)

**Optional:**

- `--quality <1-100>` (default: 80): Quality for lossy formats
- `--output <directory>` (default: `output/` next to source file): Output directory
- `--strip-exif`: Remove EXIF metadata from output

### Convert Examples

#### Convert HEIC to JPEG

```bash
python3 ipro.py convert photo.heic --format jpeg
```

#### Convert to WebP with Custom Quality

```bash
python3 ipro.py convert photo.jpg --format webp --quality 85 --output ./webp/
```

#### Batch Convert All HEIC Files

```bash
for img in *.heic; do
  python3 ipro.py convert "$img" --format jpeg
done
```

---

## Rename Command

Rename images based on actual format or EXIF metadata.

### Rename Command Usage

```bash
python3 ipro.py rename <file> [--ext] [--prefix-exif-date] [options]
```

### Rename Parameters

**Required:**

- `<file>`: Path to image file
- At least one of: `--ext` or `--prefix-exif-date`

**Optional:**

- `--output <directory>`: Output directory (default: same as source)

### Rename Examples

#### Fix Mismatched Extension

```bash
# photo.HEIC (actually JPEG) → photo.jpg
python3 ipro.py rename photo.HEIC --ext
```

#### Add EXIF Date Prefix

```bash
# photo.jpg → 2024-11-12T143000_photo.jpg
python3 ipro.py rename photo.jpg --prefix-exif-date
```

#### Combine Both Operations

```bash
# photo.HEIC (JPEG, taken 2024-11-12 14:30:00) → 2024-11-12T143000_photo.jpg
python3 ipro.py rename photo.HEIC --ext --prefix-exif-date
```

---

## Command Chaining

Chain multiple commands together using the `+` separator. Each command's output files are automatically passed as input to the next command.

### Chaining Syntax

```bash
python3 ipro.py <command1> <file> [options] + <command2> [options] + <command3> [options]
```

### How It Works

1. The first command processes the input file(s) and produces output files
2. The `+` separator marks the boundary between commands
3. Each subsequent command receives the previous command's output files as input
4. Each command can have its own `--output` directory and options

### Chaining Examples

#### Convert and Resize (Instagram Workflow)

```bash
# Convert HEIC to JPEG at 80% quality, then resize to 1080px wide
python3 ipro.py convert photo.heic --format jpeg --quality 80 + resize --width 1080
```

#### Resize and Convert to WebP

```bash
# Resize to multiple widths, then convert all to WebP
python3 ipro.py resize photo.jpg --width 300,600,1200 + convert --format webp
```

#### Three-Step Pipeline

```bash
# Resize, convert to WebP, then fix extensions
python3 ipro.py resize photo.jpg --width 300 --output ./resized + convert --format webp --output ./converted + rename --ext --output ./final
```

#### Batch Chain Processing

```bash
# Process all HEIC files: convert to JPEG + resize for web
for img in *.heic; do
  python3 ipro.py convert "$img" --format jpeg --quality 80 + resize --width 1080
done
```

### Chaining Notes

- If the first command fails (e.g., file not found), the entire chain aborts
- If a command produces no output (e.g., resize skips upscaling), subsequent commands receive no input
- Each command's `--output` directory defaults to `output/` next to the source file; chained commands reuse the same `output/` directory to avoid nesting
- The `info` command passes through its input file to the next command in the chain

---

## Batch Scripts

The `scripts/` directory contains utility scripts for batch processing:

| Script | Purpose |
| -------- | --------- |
| `rename-all.sh` | Add EXIF date prefix and correct extensions |
| `convert-all.sh` | Convert images to JPEG with sRGB profile |
| `resize-all.sh` | Resize images to specified width(s) |
| `organize-by-orientation.sh` | Organize by orientation or aspect ratio |
| `organize-by-date.sh` | Organize into subdirectories by ISO date prefix |
| `organize-all-by-date.sh` | Run date organization on all subdirectories |
| `prepare-instagram.sh` | Automated Instagram image preparation workflow |

See [scripts/README.md](scripts/README.md) for detailed usage.

### Example Workflow

```bash
# Complete image processing pipeline
source .venv/bin/activate

# 1. Rename with EXIF dates
./scripts/rename-all.sh ./photos ./renamed

# 2. Convert to JPEG with sRGB
./scripts/convert-all.sh ./renamed ./converted

# 3. Resize for web
./scripts/resize-all.sh ./converted 1080 ./final

# 4. Organize by aspect ratio
./scripts/organize-by-orientation.sh ./final ./organized --by-ratio
```

## Testing

### Manual Testing

1. **Create a test image**:

   ```bash
   python3 -c "
   from PIL import Image, ImageDraw
   img = Image.new('RGB', (1200, 800), color='lightblue')
   draw = ImageDraw.Draw(img)
   draw.rectangle([100, 100, 1100, 700], outline='navy', width=5)
   draw.ellipse([300, 200, 900, 600], fill='yellow', outline='orange', width=3)
   img.save('test_photo.jpg', 'JPEG', quality=95)
   print('Created test_photo.jpg (1200x800)')
   "
   ```

2. **Test basic resize**:

   ```bash
   python3 ipro.py resize test_photo.jpg --width 300,600,900
   ```

3. **Verify output**:

   ```bash
   ls -lh output/
   ```

4. **Test upscaling prevention**:

   ```bash
   python3 ipro.py resize test_photo.jpg --width 300,600,1500
   # Should skip 1500px with a warning
   ```

5. **Test error handling**:

   ```bash
   # Test missing file
   python3 ipro.py resize nonexistent.jpg --width 300

   # Test non-JPEG file
   touch test.png
   python3 ipro.py resize test.png --width 300
   ```

### Test Scenarios Covered

- ✓ Resize by width with multiple sizes
- ✓ Resize by height with multiple sizes
- ✓ Custom quality settings (1-100)
- ✓ Custom output directory
- ✓ Upscaling prevention with warnings
- ✓ File not found error handling
- ✓ Non-JPEG format rejection
- ✓ Mutually exclusive width/height validation
- ✓ Quality range validation
- ✓ EXIF metadata stripping
- ✓ Aspect ratio preservation

### Automated Testing

The project includes a comprehensive `pytest`-based test suite:

**Run all tests:**

```bash
python -m pytest tests/ -v
```

**Run with coverage report:**

```bash
python -m pytest tests/ --cov=ipro --cov-report=term-missing
```

**Test Coverage:**

- **Info command:** 100% coverage (69 tests)
  - 36 unit tests for helper functions
  - 33 CLI integration tests
- **Resize command:** ~95% coverage (55 tests)
  - 28 unit tests for helper functions and shared utilities
  - 27 CLI integration tests
- **Convert command:** 100% coverage (52 tests)
- **Rename command:** 100% coverage (50 tests)
- **Command chaining:** 100% coverage (31 tests)
- **Overall project:** 342 total tests

**CI/CD:**

- GitHub Actions automatically runs tests on all PRs
- Tests across Python 3.8, 3.9, 3.10, 3.11

### Test-Driven Development

This project follows TDD practices for all new features:

**Workflow:**

1. **Write tests first** - Define expected behavior through tests before implementation
2. **Watch them fail** - Confirm tests fail as expected (red)
3. **Implement feature** - Write minimal code to make tests pass (green)
4. **Refactor** - Improve code while keeping tests green
5. **Maintain coverage** - Keep coverage high (>80% on core logic)

**For new features:**

- Use PRD sections as source of truth for test requirements
- Create both unit tests (helper functions) and integration tests (CLI)
- Test edge cases: file handling, error conditions, boundary values
- Focus on EXIF handling, aspect ratios, and format conversions

**Example:** The `info` command was developed using TDD:

- First: Wrote 69 tests covering all requirements (all failing)
- Then: Implemented features until all tests passed
- Result: 100% coverage with confidence in correctness

See `TASKS.md` for current development priorities and `tests/` for examples.

## Output File Naming

ipro uses a simple, predictable naming pattern:

**Pattern**: `{basename}_{size}.{ext}`

**Examples**:

- `photo.jpg` at 300px → `photo_300.jpg`
- `vacation.jpeg` at 600px → `vacation_600.jpeg`
- `banner.JPG` at 1200px → `banner_1200.JPG`

The size suffix represents the dimension specified (width or height) in pixels.

## Error Handling

ipro provides clear error messages and appropriate exit codes:

### Exit Codes

- `0` - Success
- `1` - Unsupported format
- `2` - Invalid arguments (quality, width/height conflict, etc.)
- `3` - File not found
- `4` - Cannot read/process image

### Common Errors

**File not found:**

```text
Error: File not found: photo.jpg
```

**Unsupported format (v1.0 JPEG-only):**

```text
Error: Unsupported format. Version 1.0 supports JPEG only.
Supported extensions: .jpg, .jpeg, .JPG, .JPEG
```

**Invalid quality value:**

```text
Error: Quality must be between 1-100
```

**Both width and height specified:**

```text
Error: Cannot specify both --width and --height
```

## Technical Details

### Format Support

ipro leverages Pillow (PIL) for image processing and supports a wide range of formats:

**Info Command (Read Support):**

- ✅ **JPEG** (.jpg, .jpeg, .JPG, .JPEG) - Full support including EXIF metadata
- ✅ **PNG** (.png) - Full support
- ✅ **HEIF/HEIC** (.heic, .HEIC) - Requires `pillow-heif` package (automatically installed)
- ✅ **DNG (RAW)** (.dng) - Adobe Digital Negative format
- ✅ **BMP** (.bmp) - Windows Bitmap
- ✅ **GIF** (.gif) - Graphics Interchange Format
- ✅ **TIFF** (.tif, .tiff) - Tagged Image File Format
- ✅ **WebP** (.webp) - Modern web format
- ✅ **Other formats** - Most Pillow-compatible formats

**Resize Command (v1.0):**

- ✅ **JPEG only** (.jpg, .jpeg, .JPG, .JPEG)
- 🔜 PNG, WebP, AVIF support planned for future versions (see Roadmap)

**Notes:**

- Format detection is based on file content, not extension (e.g., a JPEG file renamed to .heic will still work)
- HEIF/HEIC support requires the `pillow-heif` package, which is included in `requirements.txt`
- Some formats may have limited EXIF support depending on how metadata is stored

### Image Processing

- **Resampling Algorithm**: Lanczos (high-quality downsampling)
- **Aspect Ratio**: Always preserved
- **Color Mode**: Converts to RGB for JPEG output
- **Transparency Handling**: Converts to white background for JPEG
- **EXIF Data**: Stripped by default for web optimization
- **ICC Profiles**: Maintained during conversion

### File System

- Creates output directory if it doesn't exist
- Supports absolute and relative paths
- Handles spaces and special characters in filenames
- Supports Unicode filenames

## Roadmap

See [PRD.md](PRD.md) for the complete product requirements and future enhancements.

### Version History

- v1.0: Info and resize commands with JPEG support
- v1.1: Rename and convert commands, HEIC/HEIF support, sRGB conversion
- v1.2: WebP output support, batch scripts, documentation updates
- v1.2.1: **Breaking** - resize uses positional file arg, Instagram script, project rename
- v1.3: Command chaining with `+` separator, source-relative `output/` default directory

### Planned Features

- v1.3: Advanced resizing (crop modes, fit modes)
- v1.4: AVIF support, metadata editing
- v1.5: Responsive web features (generate HTML srcset, picture elements)
- v1.6: Configuration files (presets, per-project config)
- v2.0: Advanced features (watermarking, filters, parallel processing)

## Development

### Project Structure

```text
ipro/
├── .github/
│   └── workflows/
│       └── test.yml          # CI/CD pipeline
├── devlog/                   # Development logs and PR descriptions
├── scripts/
│   ├── README.md            # Script documentation
│   ├── convert-all.sh       # Batch format conversion
│   ├── organize-all-by-date.sh    # Run date organization on subdirs
│   ├── organize-by-date.sh        # Organize by ISO date prefix
│   ├── organize-by-orientation.sh # Organize by orientation/ratio
│   ├── prepare-instagram.sh # Instagram image preparation workflow
│   ├── rename-all.sh        # Batch rename with EXIF dates
│   └── resize-all.sh        # Batch resize
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest configuration and fixtures
│   ├── fixtures.py          # Test image generation with synthetic EXIF
│   ├── test_info_cli.py     # Info command integration tests
│   ├── test_info_helpers.py # Info command unit tests
│   ├── test_convert_cli.py  # Convert command integration tests
│   ├── test_convert_helpers.py # Convert command unit tests
│   ├── test_rename_cli.py   # Rename command integration tests
│   ├── test_rename_helpers.py # Rename command unit tests
│   ├── test_resize_cli.py   # Resize command integration tests
│   ├── test_resize_helpers.py # Resize command unit tests
│   └── test_chain_cli.py    # Command chaining integration tests
├── ipro.py              # Main CLI tool
├── pyproject.toml           # Package config (enables pipx install)
├── requirements.txt         # Python dependencies
├── PRD.md                   # Product Requirements Document
├── TASKS.md                 # Task tracking and project status
├── DONE.md                  # Completed tasks archive
└── README.md                # This file
```

### Adding New Commands

The script uses a subcommand architecture. To add a new command:

1. Create a command handler function (e.g., `cmd_convert`)
2. Add a subparser in the `main()` function
3. Set the function as the default handler: `parser.set_defaults(func=cmd_convert)`

Example structure:

```python
def cmd_convert(args):
    """Handle the convert subcommand."""
    # Implementation here
    pass

# In main():
convert_parser = subparsers.add_parser('convert', help='Convert image formats')
convert_parser.add_argument('--format', required=True)
convert_parser.set_defaults(func=cmd_convert)
```

## Contributing

Contributions are welcome! This project follows Test-Driven Development practices.

### Development Workflow

1. **Fork and clone** the repository
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Create a branch** for your feature: `git checkout -b feature/your-feature`
4. **Write tests first** (TDD approach):
   - Unit tests in `tests/test_*_helpers.py`
   - Integration tests in `tests/test_*_cli.py`
   - Ensure tests fail before implementation
5. **Implement the feature** until tests pass
6. **Run the full test suite**: `python -m pytest tests/ -v`
7. **Check coverage**: `python -m pytest tests/ --cov=ipro --cov-report=term-missing`
8. **Commit and push** with clear commit messages
9. **Open a Pull Request** - CI will automatically run all tests

### Coding Standards

- Follow existing code style and structure
- Write descriptive docstrings for functions
- Use type hints where helpful
- Keep functions focused and testable
- Error messages should be clear and actionable
- Test coverage should remain >80% on core logic

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_info_cli.py -v

# Run with coverage
python -m pytest tests/ --cov=ipro --cov-report=html

# Run specific test
python -m pytest tests/test_info_cli.py::TestInfoCommandBasics::test_info_command_exists -v
```

### Project Priorities

See [TASKS.md](TASKS.md) for current priorities and status. Next priorities include:

1. Add field selection to `ipro info` command
2. Add `--verbose` and `--quiet` modes

For design decisions and feature requirements, refer to [PRD.md](PRD.md).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Pillow](https://pillow.readthedocs.io/) - The friendly PIL fork
- Designed for use with static site generators like [11ty](https://www.11ty.dev/)
