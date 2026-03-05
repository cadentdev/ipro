#!/usr/bin/env python3
"""
ipro - Command-line tool for responsive image processing
"""

import argparse
import sys
from pathlib import Path
from PIL import Image
from PIL import ImageCms
from PIL.ExifTags import TAGS
from PIL.TiffImagePlugin import IFDRational
import os
import json
import math
import io
import shutil
import tempfile

# Register HEIF opener if pillow-heif is available
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass  # pillow-heif not installed, HEIF support unavailable


__version__ = "1.6.0"

# Exit codes
EXIT_SUCCESS = 0
EXIT_UNSUPPORTED_FORMAT = 1
EXIT_INVALID_ARGS = 2
EXIT_FILE_NOT_FOUND = 3
EXIT_READ_ERROR = 4

# Security limits
MAX_IMAGE_PIXELS = 100_000_000  # 100 megapixels — generous but safe
MAX_INPUT_FILE_SIZE = 500 * 1024 * 1024  # 500 MB
MAX_SIZES_COUNT = 20  # Maximum number of sizes in a single resize operation

# Apply decompression bomb protection globally
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS

# Quality defaults
DEFAULT_RESIZE_QUALITY = 90
DEFAULT_CONVERT_QUALITY = 80

# Known ipro output directory names for chain detection
IPRO_OUTPUT_DIRS = {'converted', 'renamed', 'extracted', 'output'}


def is_ipro_output_dir(dirname):
    """Check if a directory name is a known ipro output directory."""
    return dirname in IPRO_OUTPUT_DIRS or dirname.startswith('resized')


def get_resize_dir_name(sizes, dimension):
    """Compute the default output directory name for resize.

    Single size: resized-{size}w or resized-{size}h
    Multiple sizes: resized
    """
    if len(sizes) == 1:
        suffix = 'w' if dimension == 'width' else 'h'
        return f"resized-{sizes[0]}{suffix}"
    return "resized"

# Supported output formats for convert command
SUPPORTED_OUTPUT_FORMATS = {
    'jpeg': '.jpg',
    'jpg': '.jpg',
    'png': '.png',
    'webp': '.webp',
}


def split_chain(argv):
    """Split command-line arguments at '+' separators into command segments.

    Args:
        argv: List of command-line arguments (without the program name).

    Returns:
        List of argument segments, each a list of strings representing
        one command invocation. Empty segments (from leading, trailing,
        or consecutive '+' tokens) are discarded.
    """
    segments = []
    current = []
    for arg in argv:
        if arg == '+':
            if current:
                segments.append(current)
            current = []
        else:
            current.append(arg)
    if current:
        segments.append(current)
    return segments


def is_supported_output_format(format_str):
    """
    Check if a format is supported for output conversion.

    Args:
        format_str: Format name (e.g., "jpeg", "png")

    Returns:
        bool: True if supported, False otherwise
    """
    return format_str.lower() in SUPPORTED_OUTPUT_FORMATS


def get_target_extension(format_str):
    """
    Get the file extension for a target format.

    Args:
        format_str: Format name (e.g., "jpeg", "png")

    Returns:
        String: Extension with dot (e.g., ".jpg") or None if unsupported
    """
    return SUPPORTED_OUTPUT_FORMATS.get(format_str.lower())


def ensure_rgb_for_jpeg(img):
    """
    Convert image to RGB mode suitable for JPEG output.

    Handles RGBA, LA, and P (palette) modes by compositing onto a white
    background. Other non-RGB modes are converted directly.

    Args:
        img: PIL Image object

    Returns:
        PIL Image object in RGB mode
    """
    if img.mode in ('RGBA', 'LA', 'P'):
        if img.mode == 'P':
            img = img.convert('RGBA')
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode in ('RGBA', 'LA'):
            if img.mode == 'LA':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1])
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    return img


def validate_output_path(output_str, input_path):
    """
    Validate an output path for security concerns.

    Checks for path traversal components, null bytes, and warns if the
    resolved output is outside the input file's parent tree.

    Args:
        output_str: The raw --output argument string
        input_path: Path object of the input file

    Returns:
        Path object for the validated output

    Raises:
        SystemExit if the path contains null bytes or '..' components
    """
    # Reject null bytes
    if '\x00' in output_str:
        print("Error: Output path contains null bytes", file=sys.stderr)
        sys.exit(EXIT_INVALID_ARGS)

    # Reject path traversal components in the original string
    # Check each component of the path for literal '..'
    raw_path = Path(output_str)
    for part in raw_path.parts:
        if part == '..':
            print("Error: Output path contains '..' traversal components", file=sys.stderr)
            sys.exit(EXIT_INVALID_ARGS)

    resolved = raw_path.resolve()

    # Warn (but don't block) if absolute path is outside input's parent tree
    if raw_path.is_absolute():
        input_parent = input_path.resolve().parent
        try:
            resolved.relative_to(input_parent)
        except ValueError:
            print(f"Warning: Output path '{output_str}' is outside the input file's directory tree",
                  file=sys.stderr)

    return resolved


def resolve_output_dir(args_output, input_path, default_dir_name):
    """
    Resolve the output directory from CLI args, input path, and subcommand default.

    If args_output is provided, use it (with security validation).
    If the input is already in an ipro output directory (chaining), go up one
    level and create default_dir_name as a sibling.
    Otherwise, create default_dir_name next to the source file.

    Args:
        args_output: The --output argument value (str or None)
        input_path: Path object of the input file
        default_dir_name: Subcommand-specific default dir name (e.g., "converted")

    Returns:
        Path object for the output directory
    """
    if args_output:
        output_path = validate_output_path(args_output, input_path)
        # Reject if the original output path is a symlink (check before resolution)
        original_path = Path(args_output)
        if original_path.is_symlink():
            print("Error: Output directory is a symlink — refusing to write", file=sys.stderr)
            sys.exit(EXIT_INVALID_ARGS)
        return output_path
    elif is_ipro_output_dir(input_path.parent.name):
        # Chaining: place output as sibling of previous output dir
        return input_path.parent.parent / default_dir_name
    else:
        return input_path.parent / default_dir_name


def validate_input_file(filepath):
    """
    Validate that an input file exists, is within size limits, and return it as a Path.

    Checks: existence, symlink warning, file size limit.

    Args:
        filepath: String or Path to the input file

    Returns:
        Path object if file exists and passes validation

    Raises:
        SystemExit with EXIT_FILE_NOT_FOUND if file doesn't exist
        SystemExit with EXIT_INVALID_ARGS if file exceeds size limit
    """
    path = Path(filepath)
    if not path.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(EXIT_FILE_NOT_FOUND)

    # Warn if input is a symlink (don't block — may be legitimate)
    if path.is_symlink():
        print(f"Warning: Input file is a symlink: {filepath}", file=sys.stderr)

    # Reject files exceeding size limit
    try:
        file_size = os.path.getsize(path)
        if file_size > MAX_INPUT_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            limit_mb = MAX_INPUT_FILE_SIZE / (1024 * 1024)
            print(f"Error: File size ({size_mb:.0f} MB) exceeds limit ({limit_mb:.0f} MB): {filepath}",
                  file=sys.stderr)
            sys.exit(EXIT_INVALID_ARGS)
    except OSError:
        pass  # If we can't stat the file, let later operations handle it

    return path


def convert_to_srgb(img):
    """
    Convert image to sRGB color profile if it has a different profile.

    Args:
        img: PIL Image object

    Returns:
        PIL Image object in sRGB color space
    """
    try:
        # Check if image has an ICC profile
        icc_profile = img.info.get('icc_profile')
        if icc_profile:
            # Create profile objects
            src_profile = ImageCms.ImageCmsProfile(io.BytesIO(icc_profile))
            srgb_profile = ImageCms.createProfile('sRGB')

            # Convert to sRGB
            img = ImageCms.profileToProfile(
                img, src_profile, srgb_profile,
                outputMode='RGB' if img.mode == 'RGB' else img.mode
            )
    except ImageCms.PyCMSError:
        # If color management conversion fails, return the original image
        pass
    return img


def _strip_gps_from_exif(exif_data):
    """
    Remove GPS metadata (tag 34853/0x8825) from EXIF data.

    GPS data contains location information that is a privacy risk.
    This is stripped by default when EXIF is preserved during conversion.

    Args:
        exif_data: PIL Exif object

    Returns:
        PIL Exif object with GPS data removed, or original if no GPS present
    """
    GPS_IFD_TAG = 0x8825  # GPSInfo tag
    if exif_data and GPS_IFD_TAG in exif_data:
        del exif_data[GPS_IFD_TAG]
        return exif_data, True
    return exif_data, False


def convert_image(source_path, output_path, target_format, quality=DEFAULT_CONVERT_QUALITY, strip_exif=False, convert_to_srgb_profile=True):
    """
    Convert an image to a different format.

    Args:
        source_path: Path to source image
        output_path: Path for output image
        target_format: Target format (e.g., "jpeg", "png")
        quality: JPEG quality 1-100 (default: 80)
        strip_exif: If True, strip EXIF metadata from output
        convert_to_srgb_profile: If True, convert to sRGB color profile (default: True)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        source_path = Path(source_path)
        output_path = Path(output_path)

        # Refuse to write through a symlink output path
        if output_path.exists() and output_path.is_symlink():
            print(f"Error: Output path is a symlink — refusing to write: {output_path}",
                  file=sys.stderr)
            return False

        with Image.open(source_path) as img:
            # Get EXIF data if we need to preserve it
            exif_data = None
            if not strip_exif:
                try:
                    exif_data = img.getexif()
                except Exception:
                    exif_data = None

                # Strip GPS data by default when preserving EXIF (privacy protection)
                if exif_data:
                    exif_data, gps_stripped = _strip_gps_from_exif(exif_data)
                    if gps_stripped:
                        print("Note: GPS metadata stripped from output (use --keep-gps to preserve)",
                              file=sys.stderr)

            # Convert to sRGB if requested
            if convert_to_srgb_profile:
                img = convert_to_srgb(img)

            # Handle color mode conversion for JPEG output
            if target_format.lower() in ('jpeg', 'jpg'):
                img = ensure_rgb_for_jpeg(img)

            # Prepare save arguments
            save_kwargs = {}
            if target_format.lower() in ('jpeg', 'jpg'):
                save_kwargs['quality'] = quality
                save_kwargs['format'] = 'JPEG'
            elif target_format.lower() == 'png':
                save_kwargs['format'] = 'PNG'
            elif target_format.lower() == 'webp':
                save_kwargs['quality'] = quality
                save_kwargs['format'] = 'WEBP'

            # Add EXIF if preserving
            if exif_data and not strip_exif and target_format.lower() in ('jpeg', 'jpg'):
                save_kwargs['exif'] = exif_data

            # Embed sRGB ICC profile for better compatibility
            if convert_to_srgb_profile:
                srgb_profile = ImageCms.createProfile('sRGB')
                save_kwargs['icc_profile'] = ImageCms.ImageCmsProfile(srgb_profile).tobytes()

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save the image
            img.save(output_path, **save_kwargs)

        return True

    except Image.DecompressionBombError:
        print(f"Error: Image exceeds pixel limit ({MAX_IMAGE_PIXELS:,} pixels) — "
              "possible decompression bomb", file=sys.stderr)
        return False
    except Exception:
        # Clean up partial output files if they were created
        try:
            if output_path.exists():
                output_path.unlink()
        except OSError:
            pass
        return False


def parse_sizes(size_str):
    """Parse comma-separated list of sizes into integers.

    Enforces MAX_SIZES_COUNT to prevent unbounded resize operations.
    """
    try:
        sizes = [int(s.strip()) for s in size_str.split(',')]
        if any(s <= 0 for s in sizes):
            raise ValueError("Sizes must be positive integers")
        if len(sizes) > MAX_SIZES_COUNT:
            raise ValueError(
                f"Too many sizes ({len(sizes)}). Maximum is {MAX_SIZES_COUNT}"
            )
        return sizes
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Invalid size format: {e}")



def get_file_size_kb(filepath):
    """Get file size in KB."""
    return os.path.getsize(filepath) / 1024


def calculate_aspect_ratio(width, height):
    """
    Calculate aspect ratio as a reduced integer ratio string.

    Args:
        width: Image width in pixels
        height: Image height in pixels

    Returns:
        String in format "W:H" (e.g., "16:9", "4:3")
    """
    gcd = math.gcd(width, height)
    ratio_w = width // gcd
    ratio_h = height // gcd
    return f"{ratio_w}:{ratio_h}"


def classify_orientation(width, height):
    """
    Classify image orientation based on dimensions.

    Args:
        width: Image width in pixels
        height: Image height in pixels

    Returns:
        String: "square", "landscape", or "portrait"
    """
    if width == height:
        return "square"
    elif width > height:
        return "landscape"
    else:
        return "portrait"


def match_common_ratio(ratio_str):
    """
    Match a ratio string against common aspect ratios.

    Args:
        ratio_str: Ratio string in format "W:H" (e.g., "16:9")

    Returns:
        String: matched common ratio name or "none"
    """
    # Define common ratios with their standard names
    common_ratios = {
        "1:1": "1:1",
        "4:3": "4:3",
        "3:4": "3:4",
        "3:2": "3:2",
        "2:3": "2:3",
        "16:9": "16:9",
        "9:16": "9:16",
        "5:4": "5:4",
        "4:5": "4:5",
        "191:100": "1.91:1",  # Instagram landscape
    }

    return common_ratios.get(ratio_str, "none")


def extract_exif_data(filepath):
    """
    Extract EXIF metadata from an image file.

    Args:
        filepath: Path to image file

    Returns:
        Dictionary of EXIF data or None if no EXIF present
    """
    try:
        with Image.open(filepath) as img:
            exif = img.getexif()

            if not exif:
                return None

            # Convert to dictionary with tag names
            exif_dict = {}
            for tag_id, value in exif.items():
                tag_name = TAGS.get(tag_id, tag_id)
                exif_dict[tag_name] = value

            return exif_dict if exif_dict else None

    except Exception:
        return None


def format_exif_curated(exif_dict):
    """
    Format curated subset of EXIF data.

    Args:
        exif_dict: Dictionary of EXIF data

    Returns:
        Dictionary with curated EXIF fields using friendly names
    """
    if not exif_dict:
        return {}

    curated = {}

    # Date taken (prefer DateTimeOriginal, fall back to DateTime)
    if 'DateTimeOriginal' in exif_dict:
        curated['date_taken'] = exif_dict['DateTimeOriginal']
    elif 'DateTime' in exif_dict:
        curated['date_taken'] = exif_dict['DateTime']

    # Camera make and model
    if 'Make' in exif_dict:
        curated['camera_make'] = exif_dict['Make']
    if 'Model' in exif_dict:
        curated['camera_model'] = exif_dict['Model']

    # Orientation
    if 'Orientation' in exif_dict:
        curated['orientation'] = exif_dict['Orientation']

    # DPI/Resolution
    if 'XResolution' in exif_dict:
        curated['dpi_x'] = exif_dict['XResolution']
    if 'YResolution' in exif_dict:
        curated['dpi_y'] = exif_dict['YResolution']
    if 'ResolutionUnit' in exif_dict:
        curated['resolution_unit'] = exif_dict['ResolutionUnit']

    return curated


def get_format_extension(format_str):
    """
    Map Pillow format name to lowercase file extension.

    Args:
        format_str: Pillow format string (e.g., "JPEG", "PNG", "HEIF")

    Returns:
        String: lowercase extension with dot (e.g., ".jpg", ".png", ".heic")
    """
    # Normalize input to uppercase
    format_upper = format_str.upper()

    # Map common formats to preferred extensions
    format_map = {
        "JPEG": ".jpg",
        "MPO": ".jpg",
        "PNG": ".png",
        "HEIF": ".heic",
        "GIF": ".gif",
        "WEBP": ".webp",
        "TIFF": ".tiff",
        "BMP": ".bmp",
        "ICO": ".ico",
        "PPM": ".ppm",
        "DNG": ".dng",
    }

    return format_map.get(format_upper, f".{format_str.lower()}")


def format_exif_date_prefix(exif_date_str):
    """
    Convert EXIF date string to filename-safe prefix.

    Args:
        exif_date_str: EXIF format date string "YYYY:MM:DD HH:MM:SS"

    Returns:
        String: Filename prefix "YYYY-MM-DDTHHMMSS_" or None if invalid
    """
    if not exif_date_str:
        return None

    try:
        # EXIF format: "YYYY:MM:DD HH:MM:SS"
        # Target format: "YYYY-MM-DDTHHMMSS_"
        parts = exif_date_str.split(' ')
        if len(parts) != 2:
            return None

        date_part = parts[0]
        time_part = parts[1]

        # Validate date format: must be YYYY:MM:DD
        date_components = date_part.split(':')
        if len(date_components) != 3:
            return None
        # Check that all components are ASCII numeric (reject Unicode digits)
        for comp in date_components:
            if not comp.isascii() or not comp.isdigit():
                return None

        # Validate time format: must be HH:MM:SS
        time_components = time_part.split(':')
        if len(time_components) != 3:
            return None
        for comp in time_components:
            if not comp.isascii() or not comp.isdigit():
                return None

        formatted_date = date_part.replace(':', '-')  # YYYY:MM:DD -> YYYY-MM-DD
        formatted_time = time_part.replace(':', '')   # HH:MM:SS -> HHMMSS

        return f"{formatted_date}T{formatted_time}_"
    except Exception:
        return None


def build_renamed_filename(original, ext=None, date_prefix=None):
    """
    Build a new filename with optional extension change and date prefix.

    Args:
        original: Original filename (string or Path)
        ext: New extension (e.g., ".jpg") or None to keep original
        date_prefix: Date prefix to prepend (e.g., "2024-11-12T143000_") or None

    Returns:
        String: New filename
    """
    # Handle Path objects
    if isinstance(original, Path):
        original = original.name

    # Get basename without extension
    path = Path(original)
    stem = path.stem
    original_ext = path.suffix

    # Use new extension or keep original
    new_ext = ext if ext is not None else original_ext

    # Build new filename
    new_name = stem + new_ext

    # Add date prefix if provided
    if date_prefix:
        new_name = date_prefix + new_name

    return new_name


def get_image_format(filepath):
    """
    Get the actual image format from file content (not extension).

    Args:
        filepath: Path to image file

    Returns:
        String: Pillow format name (e.g., "JPEG", "PNG") or None if can't read
    """
    try:
        with Image.open(filepath) as img:
            return img.format
    except Exception:
        return None


def get_image_info(filepath):
    """
    Get comprehensive information about an image file.

    Args:
        filepath: Path to image file

    Returns:
        Dictionary containing image metadata
    """
    filepath = Path(filepath)

    # Open image
    with Image.open(filepath) as img:
        # Get dimensions (EXIF orientation is already handled by Pillow in most cases)
        width, height = img.size
        image_format = img.format
        n_frames = getattr(img, 'n_frames', 1)

    # Calculate ratios and orientation
    ratio_raw = calculate_aspect_ratio(width, height)
    common_ratio = match_common_ratio(ratio_raw)
    orientation = classify_orientation(width, height)

    # Extract EXIF
    exif_data = extract_exif_data(filepath)
    has_exif = exif_data is not None and len(exif_data) > 0

    # Format curated EXIF
    exif_curated = format_exif_curated(exif_data) if has_exif else None

    # Get file metadata
    size_kb = get_file_size_kb(filepath)

    # Get creation date from EXIF if available
    creation_date = None
    if exif_curated and 'date_taken' in exif_curated:
        creation_date = exif_curated['date_taken']

    # Note: Full path disclosure in info output is intentional — this is a CLI tool
    # where the user already knows the file path. Not a security concern.
    return {
        'filename': filepath.name,
        'path': str(filepath.absolute()),
        'format': image_format,
        'frames': n_frames,
        'width': width,
        'height': height,
        'orientation': orientation,
        'ratio_raw': ratio_raw,
        'common_ratio': common_ratio,
        'size_kb': size_kb,
        'has_exif': has_exif,
        'exif': exif_curated,
        'exif_all': exif_data,
        'creation_date': creation_date,
    }


def resize_image(input_path, output_dir, sizes, dimension='width', quality=DEFAULT_RESIZE_QUALITY, preserve_filename=False):
    """
    Resize an image to multiple sizes.

    Args:
        input_path: Path to input image
        output_dir: Directory for output images
        sizes: List of target sizes
        dimension: 'width' or 'height'
        quality: JPEG quality (1-100)

    Returns:
        List of created files with metadata
    """
    # Open and validate image
    try:
        img = Image.open(input_path)
    except Image.DecompressionBombError:
        raise OSError(
            f"Image exceeds pixel limit ({MAX_IMAGE_PIXELS:,} pixels) — "
            "possible decompression bomb"
        )
    except Exception as e:
        raise OSError(f"Cannot read image: {input_path} ({e})") from e

    with img:
        # Get original dimensions
        orig_width, orig_height = img.size

        # Prepare output
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get base name and extension
        base_name = input_path.stem
        extension = input_path.suffix

        created_files = []
        skipped_sizes = []

        # Process each size
        for size in sizes:
            # Calculate new dimensions
            if dimension == 'width':
                if size > orig_width:
                    skipped_sizes.append((size, f"original is only {orig_width}px wide"))
                    continue
                new_width = size
                new_height = int((size / orig_width) * orig_height)
            else:  # height
                if size > orig_height:
                    skipped_sizes.append((size, f"original is only {orig_height}px tall"))
                    continue
                new_height = size
                new_width = int((size / orig_height) * orig_width)

            # Resize image using high-quality Lanczos resampling
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Prepare output filename
            if preserve_filename:
                output_filename = f"{base_name}{extension}"
            else:
                output_filename = f"{base_name}_{size}{extension}"
            output_path = output_dir / output_filename

            # Refuse to write through a symlink output path
            if output_path.exists() and output_path.is_symlink():
                print(f"Error: Output path is a symlink — refusing to write: {output_path}",
                      file=sys.stderr)
                continue

            # Strip EXIF by converting to RGB if needed and not saving exif
            resized_img = ensure_rgb_for_jpeg(resized_img)

            # Save without EXIF data
            resized_img.save(output_path, 'JPEG', quality=quality, optimize=True)

            # Get file size
            file_size = get_file_size_kb(output_path)

            created_files.append({
                'path': output_path,
                'filename': output_filename,
                'width': new_width,
                'height': new_height,
                'size_kb': file_size
            })

    return created_files, skipped_sizes


def extract_frames(input_path, output_dir):
    """
    Extract individual frames from a multi-frame image file.

    Supports MPO, animated GIF, APNG, animated WebP, and multi-page TIFF.

    Args:
        input_path: Path to input image
        output_dir: Directory for output frame files

    Returns:
        List of dicts with path, filename, width, height, size_kb for each frame
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    base_name = input_path.stem

    try:
        img = Image.open(input_path)
    except Image.DecompressionBombError:
        raise OSError(
            f"Image exceeds pixel limit ({MAX_IMAGE_PIXELS:,} pixels) — "
            "possible decompression bomb"
        )
    except Exception as e:
        raise OSError(f"Cannot read image: {input_path} ({e})") from e

    with img:
        n_frames = getattr(img, 'n_frames', 1)
        image_format = img.format
        pad_width = len(str(n_frames))
        if pad_width < 3:
            pad_width = 3

        # Determine output extension based on format
        if image_format in ('MPO', 'JPEG'):
            out_ext = '.jpg'
            save_format = 'JPEG'
        elif image_format == 'PNG' or image_format == 'APNG':
            out_ext = '.png'
            save_format = 'PNG'
        elif image_format == 'GIF':
            out_ext = '.png'  # Save GIF frames as PNG to preserve quality
            save_format = 'PNG'
        elif image_format == 'WEBP':
            out_ext = '.png'  # Save WebP frames as PNG to preserve quality
            save_format = 'PNG'
        elif image_format == 'TIFF':
            out_ext = '.tiff'
            save_format = 'TIFF'
        else:
            out_ext = '.png'
            save_format = 'PNG'

        created_files = []

        for frame_idx in range(n_frames):
            img.seek(frame_idx)

            # Build output filename with zero-padded numbering
            frame_num = str(frame_idx + 1).zfill(pad_width)
            output_filename = f"{base_name}_{frame_num}{out_ext}"
            output_path = output_dir / output_filename

            # Refuse to write through a symlink output path
            if output_path.exists() and output_path.is_symlink():
                print(f"Error: Output path is a symlink — refusing to write: {output_path}",
                      file=sys.stderr)
                continue

            # Convert to RGB for JPEG output
            frame_img = img.copy()
            if save_format == 'JPEG':
                frame_img = ensure_rgb_for_jpeg(frame_img)

            # Save frame
            save_kwargs = {'format': save_format}
            if save_format == 'JPEG':
                save_kwargs['quality'] = DEFAULT_CONVERT_QUALITY
                save_kwargs['optimize'] = True

            frame_img.save(output_path, **save_kwargs)

            file_size = get_file_size_kb(output_path)
            width, height = frame_img.size

            created_files.append({
                'path': output_path,
                'filename': output_filename,
                'width': width,
                'height': height,
                'size_kb': file_size,
            })

    return created_files


def serialize_exif_value(value):
    """Convert EXIF values to JSON-serializable types."""
    if isinstance(value, IFDRational):
        # Convert IFDRational to float
        return float(value)
    elif isinstance(value, bytes):
        # Convert bytes to string
        try:
            return value.decode('utf-8', errors='ignore')
        except Exception:
            return str(value)
    elif isinstance(value, (tuple, list)):
        # Recursively handle tuples and lists
        return [serialize_exif_value(v) for v in value]
    elif isinstance(value, dict):
        # Recursively handle dicts
        return {k: serialize_exif_value(v) for k, v in value.items()}
    else:
        # Return as-is for JSON-serializable types
        return value


def _format_info_json(info, args):
    """Format image info as JSON and print it.

    Args:
        info: Dictionary from get_image_info()
        args: Parsed CLI arguments (uses exif_all flag)
    """
    output_data = {
        'filename': info['filename'],
        'path': info['path'],
        'format': info['format'],
        'frames': info['frames'],
        'width': info['width'],
        'height': info['height'],
        'orientation': info['orientation'],
        'ratio_raw': info['ratio_raw'],
        'common_ratio': info['common_ratio'],
        'size_kb': round(info['size_kb'], 2),
        'has_exif': info['has_exif'],
        'creation_date': info['creation_date'] if info['creation_date'] else None,
    }

    # Add EXIF data based on flags (serialize for JSON compatibility)
    if args.exif_all and info['exif_all']:
        output_data['exif'] = {k: serialize_exif_value(v) for k, v in info['exif_all'].items()}
    elif info['exif']:
        output_data['exif'] = {k: serialize_exif_value(v) for k, v in info['exif'].items()}
    else:
        output_data['exif'] = None

    print(json.dumps(output_data))


def _format_info_csv(info):
    """Format image info as a single CSV line and print it.

    Args:
        info: Dictionary from get_image_info()
    """
    fields = [
        info['filename'],
        info['format'],
        str(info['frames']),
        str(info['width']),
        str(info['height']),
        info['orientation'],
        info['ratio_raw'],
        info['common_ratio'],
        f"{info['size_kb']:.2f}",
        info['creation_date'] if info['creation_date'] else ''
    ]
    print(','.join(fields))


def _format_info_human(info, args):
    """Format image info as human-readable text and print it.

    Args:
        info: Dictionary from get_image_info()
        args: Parsed CLI arguments (uses exif, exif_all flags)
    """
    print(f"File: {info['filename']}")
    print(f"Path: {info['path']}")
    print(f"Format: {info['format']}")
    if info['frames'] > 1:
        print(f"Frames: {info['frames']}")
    print(f"Dimensions: {info['width']}x{info['height']}")
    print(f"Orientation: {info['orientation']}")
    print(f"Aspect Ratio: {info['ratio_raw']}", end='')
    if info['common_ratio'] != 'none':
        print(f" ({info['common_ratio']})")
    else:
        print()
    print(f"File Size: {info['size_kb']:.2f} KB")
    print(f"EXIF Present: {'Yes' if info['has_exif'] else 'No'}")

    # Show EXIF data if requested or if present
    if (args.exif or args.exif_all) and info['has_exif']:
        print("\nEXIF Data:")
        if args.exif_all and info['exif_all']:
            for key, value in info['exif_all'].items():
                print(f"  {key}: {value}")
        elif info['exif']:
            for key, value in info['exif'].items():
                formatted_key = key.replace('_', ' ').title()
                print(f"  {formatted_key}: {value}")


def cmd_info(args):
    """Handle the info subcommand."""
    input_path = validate_input_file(args.file)

    # Try to get image info
    try:
        info = get_image_info(input_path)
    except Image.DecompressionBombError:
        print(f"Error: Image exceeds pixel limit ({MAX_IMAGE_PIXELS:,} pixels) — "
              "possible decompression bomb", file=sys.stderr)
        sys.exit(EXIT_UNSUPPORTED_FORMAT)
    except Exception as e:
        # If Pillow can't open it, it's unsupported or corrupt
        print(f"Error: Unsupported or unreadable image format: {args.file}", file=sys.stderr)
        sys.exit(EXIT_UNSUPPORTED_FORMAT)

    # Determine output format
    if args.json:
        _format_info_json(info, args)
    elif args.short:
        _format_info_csv(info)
    else:
        _format_info_human(info, args)

    # Return input path for chaining (info is read-only, passes through)
    return [str(input_path)]


def cmd_resize(args):
    """Handle the resize subcommand."""
    input_path = validate_input_file(args.file)

    # Validate it's a JPEG or MPO (content-based check)
    image_format = get_image_format(input_path)
    if image_format not in ('JPEG', 'MPO'):
        print(f"Error: Unsupported format. Resize supports JPEG and MPO formats.", file=sys.stderr)
        print(f"Supported extensions: .jpg, .jpeg, .JPG, .JPEG, .MPO", file=sys.stderr)
        sys.exit(EXIT_UNSUPPORTED_FORMAT)

    # Determine dimension and sizes
    if args.width and args.height:
        print("Error: Cannot specify both --width and --height", file=sys.stderr)
        sys.exit(EXIT_INVALID_ARGS)
    elif args.width:
        dimension = 'width'
        sizes = parse_sizes(args.width)
    elif args.height:
        dimension = 'height'
        sizes = parse_sizes(args.height)
    else:
        print("Error: Must specify either --width or --height", file=sys.stderr)
        sys.exit(EXIT_INVALID_ARGS)

    # Validate quality
    if not (1 <= args.quality <= 100):
        print("Error: Quality must be between 1-100", file=sys.stderr)
        sys.exit(EXIT_INVALID_ARGS)

    # Get image dimensions for output
    try:
        with Image.open(input_path) as img:
            orig_width, orig_height = img.size
    except Exception as e:
        print(f"Error: Cannot read image: {input_path}", file=sys.stderr)
        sys.exit(EXIT_READ_ERROR)

    # Resolve output directory
    dir_name = get_resize_dir_name(sizes, dimension)
    output_dir = resolve_output_dir(args.output, input_path, dir_name)

    # Print processing info
    print(f"Processing: {input_path.name} ({orig_width}x{orig_height})")
    print(f"Output directory: {output_dir}")
    print()

    # Process the image
    try:
        created_files, skipped_sizes = resize_image(
            input_path,
            output_dir,
            sizes,
            dimension=dimension,
            quality=args.quality,
            preserve_filename=(len(sizes) == 1),
        )
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(EXIT_READ_ERROR)

    # Print results
    for file_info in created_files:
        print(f"✓ Created: {file_info['filename']} "
              f"({file_info['width']}x{file_info['height']}, "
              f"{file_info['size_kb']:.0f} KB)")

    # Print warnings for skipped sizes
    if skipped_sizes:
        print()
        for size, reason in skipped_sizes:
            print(f"⚠ Skipped {size}px: {reason}")

    # Print summary
    print()
    if created_files:
        print(f"Successfully created {len(created_files)} image(s) from {input_path.name}")
    else:
        print(f"Warning: No images created (all sizes would require upscaling)")

    # Return list of created file paths for chaining
    return [str(f['path']) for f in created_files]


def cmd_rename(args):
    """Handle the rename subcommand."""
    input_path = validate_input_file(args.file)

    # Check if at least one action flag is provided
    if not args.ext and not args.prefix_exif_date:
        print("Error: At least one action flag (--ext or --prefix-exif-date) is required",
              file=sys.stderr)
        sys.exit(EXIT_INVALID_ARGS)

    # Try to read the image format
    image_format = get_image_format(input_path)
    if image_format is None:
        print(f"Error: Cannot read image: {input_path}", file=sys.stderr)
        sys.exit(EXIT_READ_ERROR)

    # Determine new extension if --ext flag is set
    new_ext = None
    if args.ext:
        new_ext = get_format_extension(image_format)

    # Determine date prefix if --prefix-exif-date flag is set
    date_prefix = None
    if args.prefix_exif_date:
        # Extract EXIF data
        exif_data = extract_exif_data(input_path)
        curated = format_exif_curated(exif_data)

        if curated and 'date_taken' in curated:
            date_prefix = format_exif_date_prefix(curated['date_taken'])
        else:
            # No EXIF date - skip with warning
            print(f"Warning: No EXIF date found in {input_path.name}, skipping",
                  file=sys.stderr)
            # If only --prefix-exif-date was requested, return input (passthrough)
            if not args.ext:
                return [str(input_path)]
            # Otherwise continue with just the extension change

    # Build new filename
    new_filename = build_renamed_filename(
        input_path.name,
        ext=new_ext,
        date_prefix=date_prefix
    )

    # Determine output directory
    output_dir = resolve_output_dir(args.output, input_path, "renamed")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build output path
    output_path = output_dir / new_filename

    # Check if source and destination are the same
    if input_path.resolve() == output_path.resolve():
        # Nothing to do - file already has correct name
        print(f"No change needed: {input_path.name}")
        return [str(input_path)]

    # Handle case-insensitive filesystems (macOS, Windows)
    # If the paths differ only by case, we need to use a temp file
    try:
        if output_path.exists() and os.path.samefile(input_path, output_path):
            # Same file on case-insensitive filesystem - rename via temp file
            # Use tempfile.mkstemp for unpredictable temp filename (L1 security fix)
            fd, temp_name = tempfile.mkstemp(
                dir=str(output_path.parent),
                prefix='.ipro_tmp_',
                suffix=output_path.suffix
            )
            temp_path = Path(temp_name)
            try:
                os.close(fd)
                shutil.copy2(input_path, temp_path)
                os.remove(input_path)
                shutil.move(str(temp_path), str(output_path))
            except Exception:
                # Clean up temp file on failure
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except OSError:
                        pass
                raise
            print(f"Created: {output_path}")
            return [str(output_path)]
    except OSError:
        pass  # Files are different, proceed normally

    # Warn if output file already exists (preserves backward compatibility)
    if output_path.exists():
        print(f"Warning: Overwriting existing file: {output_path}", file=sys.stderr)

    # Copy the file (non-destructive)
    shutil.copy2(input_path, output_path)

    # Print success message
    print(f"Created: {output_path}")

    # Return output path for chaining
    return [str(output_path)]


def cmd_convert(args):
    """Handle the convert subcommand."""
    input_path = validate_input_file(args.file)

    # Validate format option
    if not is_supported_output_format(args.format):
        print(f"Error: Unsupported output format: {args.format}", file=sys.stderr)
        print(f"Supported formats: {', '.join(sorted(set(SUPPORTED_OUTPUT_FORMATS.keys())))}",
              file=sys.stderr)
        sys.exit(EXIT_INVALID_ARGS)

    # Validate quality
    if args.quality < 1 or args.quality > 100:
        print(f"Error: Quality must be between 1-100, got {args.quality}", file=sys.stderr)
        sys.exit(EXIT_INVALID_ARGS)

    # Try to read the image to verify it's valid
    image_format = get_image_format(input_path)
    if image_format is None:
        print(f"Error: Cannot read image: {input_path}", file=sys.stderr)
        sys.exit(EXIT_READ_ERROR)

    # Warn if multi-frame image — only the primary frame will be converted
    try:
        with Image.open(input_path) as img:
            n_frames = getattr(img, 'n_frames', 1)
            if n_frames > 1:
                print(f"Warning: {input_path.name} contains {n_frames} frames; "
                      f"only the primary frame will be converted. "
                      f"Use 'extract' to export all frames.",
                      file=sys.stderr)
    except Exception:
        pass

    # Determine output path
    output_dir = resolve_output_dir(args.output, input_path, "converted")
    target_ext = get_target_extension(args.format)
    output_filename = input_path.stem + target_ext
    output_path = output_dir / output_filename

    # Check if output file already exists
    if output_path.exists():
        print(f"Warning: Overwriting existing file: {output_path}", file=sys.stderr)

    # Create output directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)

    # Convert the image
    success = convert_image(
        input_path,
        output_path,
        args.format,
        quality=args.quality,
        strip_exif=args.strip_exif
    )

    if success:
        print(f"Created: {output_path}")
        return [str(output_path)]
    else:
        print(f"Error: Failed to convert image", file=sys.stderr)
        sys.exit(EXIT_READ_ERROR)


def cmd_extract(args):
    """Handle the extract subcommand."""
    input_path = validate_input_file(args.file)

    # Resolve output directory
    output_dir = resolve_output_dir(args.output, input_path, "extracted")

    # Check frame count
    try:
        with Image.open(input_path) as img:
            n_frames = getattr(img, 'n_frames', 1)
    except Exception as e:
        print(f"Error: Cannot read image: {input_path}", file=sys.stderr)
        sys.exit(EXIT_READ_ERROR)

    if n_frames == 1:
        print(f"Note: {input_path.name} contains only 1 frame.")

    # Extract frames
    try:
        created_files = extract_frames(input_path, output_dir)
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(EXIT_READ_ERROR)

    # Print results
    for file_info in created_files:
        print(f"Created: {file_info['filename']} "
              f"({file_info['width']}x{file_info['height']}, "
              f"{file_info['size_kb']:.0f} KB)")

    # Print summary
    print()
    print(f"Extracted {len(created_files)} frame(s) from {input_path.name}")

    # Return list of created file paths for chaining
    return [str(f['path']) for f in created_files]


def main():
    """Main entry point for ipro CLI."""
    # Save current directory to restore after processing
    original_dir = os.getcwd()

    try:
        _main_impl()
    finally:
        # Restore original directory
        os.chdir(original_dir)


def _create_parser():
    """Create and return the argument parser with all subcommands.

    This is extracted from _main_impl() so the parser can be reused
    for chain execution (parsing each segment independently).

    Returns:
        argparse.ArgumentParser with all subcommand parsers configured.
    """
    parser = argparse.ArgumentParser(
        description='ipro - Command-line tool for responsive image processing',
        epilog=(
            'Use "ipro <command> --help" for more information about a command.\n'
            'Chain commands with +: ipro resize img.jpg --width 300 + convert --format webp'
        )
    )

    parser.add_argument('--version', '-v', action='version', version=f'ipro {__version__}')

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    _add_info_parser(subparsers)
    _add_resize_parser(subparsers)
    _add_rename_parser(subparsers)
    _add_convert_parser(subparsers)
    _add_extract_parser(subparsers)

    return parser


def _add_info_parser(subparsers):
    """Add the info subcommand parser."""
    info_parser = subparsers.add_parser(
        'info',
        help='Display image information and metadata',
        description='Inspect an image file and report metadata, orientation, and aspect ratio'
    )
    info_parser.add_argument('file', help='Path to image file')
    info_parser.add_argument('--json', action='store_true', help='Output in JSON format')
    info_parser.add_argument('--short', action='store_true', help='Output as a single CSV line')
    info_parser.add_argument('--exif', action='store_true', help='Show curated EXIF metadata')
    info_parser.add_argument('--exif-all', action='store_true', help='Show all EXIF metadata tags')
    info_parser.set_defaults(func=cmd_info)


def _add_resize_parser(subparsers):
    """Add the resize subcommand parser."""
    resize_parser = subparsers.add_parser(
        'resize',
        help='Resize images to multiple dimensions',
        description='Resize an image to multiple widths or heights while maintaining aspect ratio'
    )
    resize_parser.add_argument('--width', type=str,
                               help='Comma-separated list of target widths (e.g., 300,600,900)')
    resize_parser.add_argument('--height', type=str,
                               help='Comma-separated list of target heights (e.g., 400,800)')
    resize_parser.add_argument('file', help='Path to input image file')
    resize_parser.add_argument('--output', default=None,
                               help='Output directory (default: resized-{size}{w|h}/ or resized/)')
    resize_parser.add_argument('--quality', type=int, default=DEFAULT_RESIZE_QUALITY,
                               help=f'JPEG quality 1-100 (default: {DEFAULT_RESIZE_QUALITY})')
    resize_parser.set_defaults(func=cmd_resize)


def _add_rename_parser(subparsers):
    """Add the rename subcommand parser."""
    rename_parser = subparsers.add_parser(
        'rename',
        help='Rename image files based on format or EXIF data',
        description='Rename images by correcting extensions or adding EXIF date prefixes'
    )
    rename_parser.add_argument('file', help='Path to image file')
    rename_parser.add_argument('--ext', action='store_true',
                               help='Correct file extension based on actual image format')
    rename_parser.add_argument('--prefix-exif-date', action='store_true',
                               help='Prepend EXIF date to filename (format: YYYY-MM-DDTHHMMSS_)')
    rename_parser.add_argument('--output', help='Output directory (default: renamed/)')
    rename_parser.set_defaults(func=cmd_rename)


def _add_convert_parser(subparsers):
    """Add the convert subcommand parser."""
    convert_parser = subparsers.add_parser(
        'convert',
        help='Convert images between formats',
        description='Convert images to different formats (e.g., HEIC to JPEG)'
    )
    convert_parser.add_argument('file', help='Path to source image file')
    convert_parser.add_argument('--format', '-f', required=True,
                                help='Target format (jpeg, jpg, png, webp)')
    convert_parser.add_argument('--output', default=None,
                                help='Output directory (default: converted/)')
    convert_parser.add_argument('--quality', type=int, default=DEFAULT_CONVERT_QUALITY,
                                help=f'JPEG quality 1-100 (default: {DEFAULT_CONVERT_QUALITY})')
    convert_parser.add_argument('--strip-exif', action='store_true',
                                help='Remove EXIF metadata from output')
    convert_parser.set_defaults(func=cmd_convert)


def _add_extract_parser(subparsers):
    """Add the extract subcommand parser."""
    extract_parser = subparsers.add_parser(
        'extract',
        help='Extract frames from multi-frame images',
        description='Export individual frames from multi-frame image formats '
                    '(MPO, animated GIF, APNG, animated WebP, multi-page TIFF)'
    )
    extract_parser.add_argument('file', help='Path to image file')
    extract_parser.add_argument('--output', default=None,
                                help='Output directory (default: extracted/)')
    extract_parser.set_defaults(func=cmd_extract)


def _execute_chain(segments):
    """Execute a chain of commands, forwarding output file paths between steps.

    For each segment after the first, the 'file' positional argument is
    auto-injected from the previous command's output. When a command produces
    multiple output files (e.g., resize with multiple widths), the next
    command is executed once per file.

    Args:
        segments: List of argument segments from split_chain().
                  Each segment is a list of strings (command + args).
    """
    parser = _create_parser()
    output_files = None

    for i, segment in enumerate(segments):
        # TOCTOU detection: verify intermediate files still exist before passing
        # to the next command in the chain
        if output_files is not None and i > 0:
            missing = [f for f in output_files if not Path(f).exists()]
            if missing:
                for mf in missing:
                    print(f"Error: Intermediate file disappeared during chain: {mf}",
                          file=sys.stderr)
                sys.exit(EXIT_READ_ERROR)

        if output_files is not None:
            # Chained command: inject file from previous output
            if not output_files:
                # Previous command produced no output files (e.g., all resize sizes skipped)
                return
            next_output_files = []
            for input_file in output_files:
                # Build full args: subcommand_name + input_file + remaining_args
                full_segment = [segment[0], input_file] + segment[1:]
                try:
                    args = parser.parse_args(full_segment)
                except SystemExit as e:
                    sys.exit(e.code)
                if not args.command:
                    print("Error: Invalid command in chain", file=sys.stderr)
                    sys.exit(EXIT_INVALID_ARGS)
                try:
                    result = args.func(args)
                except SystemExit as e:
                    sys.exit(e.code)
                if result:
                    next_output_files.extend(result)
            output_files = next_output_files
        else:
            # First command: parse normally
            try:
                args = parser.parse_args(segment)
            except SystemExit as e:
                sys.exit(e.code)
            if not args.command:
                parser.print_help()
                sys.exit(EXIT_SUCCESS)
            try:
                output_files = args.func(args)
            except SystemExit as e:
                sys.exit(e.code)
            if output_files is None:
                output_files = []


def _main_impl():
    """Implementation of main CLI logic."""
    argv = sys.argv[1:]
    segments = split_chain(argv)

    if not segments:
        # No arguments at all - show help
        parser = _create_parser()
        parser.print_help()
        sys.exit(EXIT_SUCCESS)

    if len(segments) == 1:
        # Single command (no chain) - use standard argparse flow
        parser = _create_parser()
        args = parser.parse_args()

        # If no command specified, show help
        if not args.command:
            parser.print_help()
            sys.exit(EXIT_SUCCESS)

        # Execute the command
        args.func(args)
    else:
        # Multiple commands chained with '+'
        _execute_chain(segments)


if __name__ == '__main__':
    main()
