# ipro

CLI tool for responsive image processing — resize, convert, rename, and chain operations from the command line.

## Install

```bash
pipx install ipro-cli
# or
pip install ipro-cli
```

## Commands

| Command | Description |
|---------|-------------|
| `ipro info` | Image metadata — dimensions, format, EXIF, aspect ratio |
| `ipro resize` | Resize by width or height, preserving aspect ratio |
| `ipro convert` | Convert between JPEG, PNG, WebP, with quality control |
| `ipro rename` | Fix extensions, add EXIF date prefix |
| `ipro extract` | Extract frames from MPO, GIF, APNG, WebP, TIFF |

## Quick Examples

```bash
# Inspect an image
ipro info photo.jpg

# Resize to 1080px wide
ipro resize photo.jpg --width 1080

# Convert HEIC to JPEG
ipro convert photo.heic --format jpeg --quality 85

# Convert to WebP for web optimization
ipro convert photo.jpg --format webp --quality 80

# Chain commands: convert then resize in one pass
ipro convert photo.heic --format jpeg --quality 80 + resize --width 1080

# Batch process a directory
for img in *.jpg; do ipro resize "$img" --width 1500; done
```

## Format Support

**Read:** JPEG, PNG, HEIC/HEIF, WebP, GIF, TIFF, BMP, DNG, MPO, APNG
**Write:** JPEG, PNG, WebP

## Features

- Chain commands with `+` — `resize + convert` in a single pass
- Smart upscaling prevention — skips sizes larger than the original
- Lanczos resampling for high-quality output
- Automatic sRGB color profile conversion
- EXIF stripping by default for web optimization
- Supports iPhone HEIC photos via pillow-heif

## Requirements

- Python 3.8+

## Links

- [Full documentation](https://github.com/cadentdev/ipro#readme)
- [Source code](https://github.com/cadentdev/ipro)
- [Issue tracker](https://github.com/cadentdev/ipro/issues)
- [Changelog](https://github.com/cadentdev/ipro/blob/main/CHANGELOG.md)

## License

MIT
