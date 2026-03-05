"""Unit tests for ipro convert helper functions."""

import pytest
from pathlib import Path
from PIL import Image
import io

# Import the helper functions we'll be testing (these don't exist yet - TDD!)
try:
    from ipro import (
        get_target_extension,
        is_supported_output_format,
        convert_image,
        SUPPORTED_OUTPUT_FORMATS,
    )
except ImportError:
    # These functions don't exist yet - we're doing TDD
    get_target_extension = None
    is_supported_output_format = None
    convert_image = None
    SUPPORTED_OUTPUT_FORMATS = None


class TestSupportedOutputFormats:
    """Test supported output format validation."""

    def test_supported_formats_constant_exists(self):
        """Test that SUPPORTED_OUTPUT_FORMATS constant is defined."""
        assert SUPPORTED_OUTPUT_FORMATS is not None, "SUPPORTED_OUTPUT_FORMATS not defined"
        assert isinstance(SUPPORTED_OUTPUT_FORMATS, (list, tuple, set, dict))

    def test_jpeg_is_supported(self):
        """Test that JPEG is a supported output format."""
        assert is_supported_output_format is not None, "is_supported_output_format not implemented"
        assert is_supported_output_format("jpeg") is True

    def test_jpg_is_supported(self):
        """Test that jpg alias is supported."""
        assert is_supported_output_format is not None
        assert is_supported_output_format("jpg") is True

    def test_png_is_supported(self):
        """Test that PNG is a supported output format."""
        assert is_supported_output_format is not None
        assert is_supported_output_format("png") is True

    def test_uppercase_format_is_supported(self):
        """Test that uppercase format names work."""
        assert is_supported_output_format is not None
        assert is_supported_output_format("JPEG") is True
        assert is_supported_output_format("PNG") is True

    def test_unsupported_format(self):
        """Test that unsupported formats return False."""
        assert is_supported_output_format is not None
        assert is_supported_output_format("avif") is False
        assert is_supported_output_format("xyz") is False


class TestGetTargetExtension:
    """Test getting file extension for target format."""

    def test_get_target_extension_jpeg(self):
        """Test JPEG format returns .jpg extension."""
        assert get_target_extension is not None, "get_target_extension not implemented"
        assert get_target_extension("jpeg") == ".jpg"

    def test_get_target_extension_jpg(self):
        """Test jpg alias returns .jpg extension."""
        assert get_target_extension is not None
        assert get_target_extension("jpg") == ".jpg"

    def test_get_target_extension_png(self):
        """Test PNG format returns .png extension."""
        assert get_target_extension is not None
        assert get_target_extension("png") == ".png"

    def test_get_target_extension_uppercase(self):
        """Test uppercase format names work."""
        assert get_target_extension is not None
        assert get_target_extension("JPEG") == ".jpg"
        assert get_target_extension("PNG") == ".png"

    def test_get_target_extension_unsupported(self):
        """Test unsupported format returns None."""
        assert get_target_extension is not None
        assert get_target_extension("xyz") is None


class TestConvertImage:
    """Test core image conversion functionality."""

    def test_convert_image_jpeg_to_png(self, sample_square_image, temp_dir):
        """Test converting JPEG to PNG."""
        assert convert_image is not None, "convert_image not implemented"

        output_path = temp_dir / "output.png"
        result = convert_image(
            sample_square_image,
            output_path,
            target_format="png"
        )

        assert result is True
        assert output_path.exists()
        # Verify it's actually a PNG
        with Image.open(output_path) as img:
            assert img.format == "PNG"

    def test_convert_image_preserves_dimensions(self, sample_landscape_image, temp_dir):
        """Test that conversion preserves image dimensions."""
        assert convert_image is not None

        output_path = temp_dir / "output.png"
        convert_image(sample_landscape_image, output_path, target_format="png")

        with Image.open(sample_landscape_image) as original:
            original_size = original.size

        with Image.open(output_path) as converted:
            assert converted.size == original_size

    def test_convert_image_with_quality(self, sample_square_image, temp_dir):
        """Test conversion with quality setting."""
        assert convert_image is not None

        output_high = temp_dir / "high_quality.jpg"
        output_low = temp_dir / "low_quality.jpg"

        convert_image(sample_square_image, output_high, target_format="jpeg", quality=95)
        convert_image(sample_square_image, output_low, target_format="jpeg", quality=50)

        # Higher quality should generally produce larger file
        # (not always guaranteed, but usually true)
        assert output_high.exists()
        assert output_low.exists()

    def test_convert_image_strip_exif(self, sample_image_with_exif, temp_dir):
        """Test that strip_exif removes EXIF data."""
        assert convert_image is not None

        output_path = temp_dir / "stripped.jpg"
        convert_image(
            sample_image_with_exif,
            output_path,
            target_format="jpeg",
            strip_exif=True
        )

        with Image.open(output_path) as img:
            exif = img.getexif()
            # EXIF should be empty or None
            assert not exif or len(exif) == 0

    def test_convert_image_preserve_exif_default(self, sample_image_with_exif, temp_dir):
        """Test that EXIF is preserved by default."""
        assert convert_image is not None

        output_path = temp_dir / "preserved.jpg"
        convert_image(
            sample_image_with_exif,
            output_path,
            target_format="jpeg",
            strip_exif=False
        )

        with Image.open(output_path) as img:
            exif = img.getexif()
            # EXIF should have some data
            assert exif and len(exif) > 0

    def test_convert_image_png_to_jpeg(self, sample_png_image, temp_dir):
        """Test converting PNG to JPEG."""
        assert convert_image is not None

        output_path = temp_dir / "from_png.jpg"
        result = convert_image(sample_png_image, output_path, target_format="jpeg")

        assert result is True
        assert output_path.exists()
        with Image.open(output_path) as img:
            assert img.format == "JPEG"

    def test_convert_image_invalid_source(self, temp_dir):
        """Test handling invalid source file."""
        assert convert_image is not None

        fake_source = temp_dir / "nonexistent.jpg"
        output_path = temp_dir / "output.png"

        result = convert_image(fake_source, output_path, target_format="png")
        assert result is False

    def test_convert_image_corrupted_source(self, sample_non_image_file, temp_dir):
        """Test handling corrupted/non-image source."""
        assert convert_image is not None

        output_path = temp_dir / "output.png"
        result = convert_image(sample_non_image_file, output_path, target_format="png")
        assert result is False


class TestConvertImageColorModes:
    """Test conversion with various color modes."""

    def test_convert_rgba_to_jpeg(self, temp_dir):
        """Test converting RGBA PNG to JPEG (requires background fill)."""
        assert convert_image is not None

        # Create RGBA image with transparency
        rgba_img = Image.new('RGBA', (100, 100), (255, 0, 0, 128))
        rgba_path = temp_dir / "rgba.png"
        rgba_img.save(rgba_path, 'PNG')

        output_path = temp_dir / "from_rgba.jpg"
        result = convert_image(rgba_path, output_path, target_format="jpeg")

        assert result is True
        assert output_path.exists()
        with Image.open(output_path) as img:
            assert img.mode == "RGB"

    def test_convert_grayscale_to_jpeg(self, temp_dir):
        """Test converting grayscale image to JPEG."""
        assert convert_image is not None

        # Create grayscale image
        gray_img = Image.new('L', (100, 100), 128)
        gray_path = temp_dir / "gray.png"
        gray_img.save(gray_path, 'PNG')

        output_path = temp_dir / "from_gray.jpg"
        result = convert_image(gray_path, output_path, target_format="jpeg")

        assert result is True
        assert output_path.exists()

    def test_convert_palette_to_jpeg(self, temp_dir):
        """Test converting palette image to JPEG."""
        assert convert_image is not None

        # Create palette image
        p_img = Image.new('P', (100, 100))
        p_path = temp_dir / "palette.png"
        p_img.save(p_path, 'PNG')

        output_path = temp_dir / "from_palette.jpg"
        result = convert_image(p_path, output_path, target_format="jpeg")

        assert result is True
        assert output_path.exists()
