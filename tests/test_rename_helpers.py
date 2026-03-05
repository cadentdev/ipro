"""Unit tests for ipro rename helper functions."""

import pytest
from pathlib import Path

# Import the helper functions we'll be testing (these don't exist yet - TDD!)
try:
    from ipro import (
        get_format_extension,
        format_exif_date_prefix,
        build_renamed_filename,
        get_image_format,
    )
except ImportError:
    # These functions don't exist yet - we're doing TDD
    get_format_extension = None
    format_exif_date_prefix = None
    build_renamed_filename = None
    get_image_format = None


class TestFormatExtensionMapping:
    """Test mapping Pillow format names to file extensions."""

    def test_get_format_extension_jpeg(self):
        """Test JPEG format maps to .jpg extension."""
        assert get_format_extension is not None, "get_format_extension not implemented"
        assert get_format_extension("JPEG") == ".jpg"

    def test_get_format_extension_png(self):
        """Test PNG format maps to .png extension."""
        assert get_format_extension is not None
        assert get_format_extension("PNG") == ".png"

    def test_get_format_extension_heif(self):
        """Test HEIF format maps to .heic extension."""
        assert get_format_extension is not None
        assert get_format_extension("HEIF") == ".heic"

    def test_get_format_extension_gif(self):
        """Test GIF format maps to .gif extension."""
        assert get_format_extension is not None
        assert get_format_extension("GIF") == ".gif"

    def test_get_format_extension_webp(self):
        """Test WEBP format maps to .webp extension."""
        assert get_format_extension is not None
        assert get_format_extension("WEBP") == ".webp"

    def test_get_format_extension_tiff(self):
        """Test TIFF format maps to .tiff extension."""
        assert get_format_extension is not None
        assert get_format_extension("TIFF") == ".tiff"

    def test_get_format_extension_bmp(self):
        """Test BMP format maps to .bmp extension."""
        assert get_format_extension is not None
        assert get_format_extension("BMP") == ".bmp"

    def test_get_format_extension_lowercase_input(self):
        """Test that lowercase format input still works."""
        assert get_format_extension is not None
        assert get_format_extension("jpeg") == ".jpg"

    def test_get_format_extension_unknown_format(self):
        """Test unknown format returns lowercase with dot prefix."""
        assert get_format_extension is not None
        # Unknown formats should return .{format} in lowercase
        result = get_format_extension("UNKNOWNFORMAT")
        assert result == ".unknownformat"


class TestExifDateFormatting:
    """Test EXIF date string to filename prefix conversion."""

    def test_format_exif_date_prefix_standard(self):
        """Test standard EXIF date format conversion."""
        assert format_exif_date_prefix is not None, "format_exif_date_prefix not implemented"
        # EXIF format: "YYYY:MM:DD HH:MM:SS"
        result = format_exif_date_prefix("2024:11:12 14:30:00")
        assert result == "2024-11-12T143000_"

    def test_format_exif_date_prefix_no_seconds(self):
        """Test EXIF date without seconds."""
        assert format_exif_date_prefix is not None
        result = format_exif_date_prefix("2023:12:15 14:23:05")
        assert result == "2023-12-15T142305_"

    def test_format_exif_date_prefix_midnight(self):
        """Test EXIF date at midnight."""
        assert format_exif_date_prefix is not None
        result = format_exif_date_prefix("2024:01:01 00:00:00")
        assert result == "2024-01-01T000000_"

    def test_format_exif_date_prefix_end_of_day(self):
        """Test EXIF date at end of day."""
        assert format_exif_date_prefix is not None
        result = format_exif_date_prefix("2024:12:31 23:59:59")
        assert result == "2024-12-31T235959_"

    def test_format_exif_date_prefix_none_input(self):
        """Test None input returns None."""
        assert format_exif_date_prefix is not None
        result = format_exif_date_prefix(None)
        assert result is None

    def test_format_exif_date_prefix_empty_string(self):
        """Test empty string returns None."""
        assert format_exif_date_prefix is not None
        result = format_exif_date_prefix("")
        assert result is None

    def test_format_exif_date_prefix_invalid_format(self):
        """Test invalid date format returns None."""
        assert format_exif_date_prefix is not None
        result = format_exif_date_prefix("invalid date")
        assert result is None

    def test_format_exif_date_prefix_no_colons_in_output(self):
        """Test that output contains no colons (macOS-safe)."""
        assert format_exif_date_prefix is not None
        result = format_exif_date_prefix("2024:11:12 14:30:00")
        assert ":" not in result


class TestBuildRenamedFilename:
    """Test building renamed filenames with various transformations."""

    def test_build_renamed_filename_ext_only(self):
        """Test renaming with extension change only."""
        assert build_renamed_filename is not None, "build_renamed_filename not implemented"
        result = build_renamed_filename("photo.HEIC", ext=".jpg")
        assert result == "photo.jpg"

    def test_build_renamed_filename_date_prefix_only(self):
        """Test renaming with date prefix only."""
        assert build_renamed_filename is not None
        result = build_renamed_filename("photo.jpg", date_prefix="2024-11-12T143000_")
        assert result == "2024-11-12T143000_photo.jpg"

    def test_build_renamed_filename_both_ext_and_date(self):
        """Test renaming with both extension and date prefix."""
        assert build_renamed_filename is not None
        result = build_renamed_filename(
            "photo.HEIC",
            ext=".jpg",
            date_prefix="2024-11-12T143000_"
        )
        assert result == "2024-11-12T143000_photo.jpg"

    def test_build_renamed_filename_preserves_basename(self):
        """Test that original basename is preserved."""
        assert build_renamed_filename is not None
        result = build_renamed_filename("my_vacation_photo.HEIC", ext=".jpg")
        assert result == "my_vacation_photo.jpg"

    def test_build_renamed_filename_no_changes(self):
        """Test with no extension or date prefix returns original."""
        assert build_renamed_filename is not None
        result = build_renamed_filename("photo.jpg")
        assert result == "photo.jpg"

    def test_build_renamed_filename_path_object(self):
        """Test with Path object input."""
        assert build_renamed_filename is not None
        result = build_renamed_filename(Path("/path/to/photo.HEIC"), ext=".jpg")
        assert result == "photo.jpg"

    def test_build_renamed_filename_multiple_dots(self):
        """Test filename with multiple dots."""
        assert build_renamed_filename is not None
        result = build_renamed_filename("photo.backup.HEIC", ext=".jpg")
        assert result == "photo.backup.jpg"

    def test_build_renamed_filename_uppercase_to_lowercase(self):
        """Test that HEIC (uppercase) becomes heic (lowercase) when same format."""
        assert build_renamed_filename is not None
        result = build_renamed_filename("photo.HEIC", ext=".heic")
        assert result == "photo.heic"

    def test_build_renamed_filename_spaces_in_name(self):
        """Test filename with spaces."""
        assert build_renamed_filename is not None
        result = build_renamed_filename("my photo.HEIC", ext=".jpg")
        assert result == "my photo.jpg"


class TestGetImageFormat:
    """Test reading actual image format from file content."""

    def test_get_image_format_jpeg(self, sample_square_image):
        """Test detecting JPEG format."""
        assert get_image_format is not None, "get_image_format not implemented"
        result = get_image_format(sample_square_image)
        assert result == "JPEG"

    def test_get_image_format_png(self, sample_png_image):
        """Test detecting PNG format."""
        assert get_image_format is not None
        result = get_image_format(sample_png_image)
        assert result == "PNG"

    def test_get_image_format_mismatched_extension(self, temp_dir):
        """Test detecting format when extension doesn't match content."""
        from PIL import Image
        # Create a JPEG but save with .heic extension
        img = Image.new('RGB', (100, 100), (255, 0, 0))
        fake_heic = temp_dir / "fake.heic"
        img.save(fake_heic, 'JPEG')

        assert get_image_format is not None
        result = get_image_format(fake_heic)
        assert result == "JPEG"  # Should detect actual format, not extension

    def test_get_image_format_invalid_file(self, sample_non_image_file):
        """Test error handling for non-image file."""
        assert get_image_format is not None
        result = get_image_format(sample_non_image_file)
        assert result is None

    def test_get_image_format_nonexistent_file(self, temp_dir):
        """Test error handling for non-existent file."""
        assert get_image_format is not None
        result = get_image_format(temp_dir / "does_not_exist.jpg")
        assert result is None


class TestExtractExifDateForRename:
    """Test extracting EXIF date specifically for rename operations."""

    def test_extract_date_from_exif_with_date(self, sample_image_with_exif):
        """Test extracting date from image with EXIF."""
        # We'll reuse existing extract_exif_data and format_exif_curated
        from ipro import extract_exif_data, format_exif_curated

        exif = extract_exif_data(sample_image_with_exif)
        assert exif is not None
        curated = format_exif_curated(exif)
        assert 'date_taken' in curated

    def test_no_date_in_exif_without_date(self, temp_dir):
        """Test handling image without date in EXIF."""
        from .fixtures import create_test_image_file, EXIF_DATA_NO_DATE
        from ipro import extract_exif_data, format_exif_curated

        # Create image with EXIF but no date
        img_path = create_test_image_file(
            800, 600,
            directory=temp_dir,
            filename='no_date.jpg',
            exif_data=EXIF_DATA_NO_DATE
        )

        exif = extract_exif_data(img_path)
        curated = format_exif_curated(exif)
        assert 'date_taken' not in curated

    def test_no_date_in_image_without_exif(self, sample_image_no_exif):
        """Test handling image without any EXIF."""
        from ipro import extract_exif_data, format_exif_curated

        exif = extract_exif_data(sample_image_no_exif)
        curated = format_exif_curated(exif)
        assert 'date_taken' not in curated
