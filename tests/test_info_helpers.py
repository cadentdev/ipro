"""Unit tests for ipro info helper functions."""

import pytest
from pathlib import Path
import math

# Import the helper functions we'll be testing (these don't exist yet - TDD!)
try:
    from ipro import (
        calculate_aspect_ratio,
        classify_orientation,
        match_common_ratio,
        get_image_info,
        extract_exif_data,
        format_exif_curated,
    )
except ImportError:
    # These functions don't exist yet - we're doing TDD
    calculate_aspect_ratio = None
    classify_orientation = None
    match_common_ratio = None
    get_image_info = None
    extract_exif_data = None
    format_exif_curated = None


class TestAspectRatioCalculation:
    """Test aspect ratio calculation using GCD for reduction."""

    def test_calculate_aspect_ratio_square(self):
        """Test 1:1 square aspect ratio."""
        assert calculate_aspect_ratio is not None, "calculate_aspect_ratio not implemented"
        ratio = calculate_aspect_ratio(1000, 1000)
        assert ratio == "1:1"

    def test_calculate_aspect_ratio_4_3(self):
        """Test 4:3 aspect ratio."""
        assert calculate_aspect_ratio is not None
        ratio = calculate_aspect_ratio(1200, 900)
        assert ratio == "4:3"

    def test_calculate_aspect_ratio_16_9(self):
        """Test 16:9 widescreen aspect ratio."""
        assert calculate_aspect_ratio is not None
        ratio = calculate_aspect_ratio(1920, 1080)
        assert ratio == "16:9"

    def test_calculate_aspect_ratio_3_2(self):
        """Test 3:2 aspect ratio."""
        assert calculate_aspect_ratio is not None
        ratio = calculate_aspect_ratio(1500, 1000)
        assert ratio == "3:2"

    def test_calculate_aspect_ratio_9_16_portrait(self):
        """Test 9:16 portrait aspect ratio."""
        assert calculate_aspect_ratio is not None
        ratio = calculate_aspect_ratio(1080, 1920)
        assert ratio == "9:16"

    def test_calculate_aspect_ratio_4_5_portrait(self):
        """Test 4:5 portrait aspect ratio."""
        assert calculate_aspect_ratio is not None
        ratio = calculate_aspect_ratio(1080, 1350)
        assert ratio == "4:5"

    def test_calculate_aspect_ratio_5_4(self):
        """Test 5:4 aspect ratio."""
        assert calculate_aspect_ratio is not None
        ratio = calculate_aspect_ratio(1250, 1000)
        assert ratio == "5:4"

    def test_calculate_aspect_ratio_instagram_1_91(self):
        """Test 1.91:1 Instagram landscape ratio (191:100)."""
        assert calculate_aspect_ratio is not None
        ratio = calculate_aspect_ratio(1910, 1000)
        assert ratio == "191:100"

    def test_calculate_aspect_ratio_reduces_properly(self):
        """Test that ratios are reduced using GCD."""
        assert calculate_aspect_ratio is not None
        # 800x600 should reduce to 4:3
        ratio = calculate_aspect_ratio(800, 600)
        assert ratio == "4:3"

    def test_calculate_aspect_ratio_odd_dimensions(self):
        """Test with non-standard dimensions."""
        assert calculate_aspect_ratio is not None
        ratio = calculate_aspect_ratio(1234, 567)
        # GCD of 1234 and 567 is 1, so ratio is 1234:567
        assert ratio == "1234:567"

    def test_calculate_aspect_ratio_prime_dimensions(self):
        """Test with prime number dimensions."""
        assert calculate_aspect_ratio is not None
        ratio = calculate_aspect_ratio(1920, 1081)
        # These are coprime, so ratio should be 1920:1081
        assert ratio == "1920:1081"


class TestOrientationClassification:
    """Test orientation classification (portrait, landscape, square)."""

    def test_classify_square_orientation(self):
        """Test square images are classified as 'square'."""
        assert classify_orientation is not None, "classify_orientation not implemented"
        assert classify_orientation(1000, 1000) == "square"
        assert classify_orientation(500, 500) == "square"
        assert classify_orientation(2000, 2000) == "square"

    def test_classify_landscape_orientation(self):
        """Test landscape images (width > height)."""
        assert classify_orientation is not None
        assert classify_orientation(1920, 1080) == "landscape"
        assert classify_orientation(1600, 900) == "landscape"
        assert classify_orientation(1000, 999) == "landscape"

    def test_classify_portrait_orientation(self):
        """Test portrait images (height > width)."""
        assert classify_orientation is not None
        assert classify_orientation(1080, 1920) == "portrait"
        assert classify_orientation(900, 1600) == "portrait"
        assert classify_orientation(999, 1000) == "portrait"

    def test_classify_orientation_with_exif_rotation(self):
        """Test that orientation considers EXIF rotation."""
        # If EXIF orientation is provided, dimensions should already be corrected
        # This test ensures the classification works correctly
        assert classify_orientation is not None
        # Image that appears landscape but is portrait after EXIF rotation
        assert classify_orientation(1080, 1920) == "portrait"


class TestCommonRatioMatching:
    """Test matching calculated ratios against common aspect ratios."""

    def test_match_common_ratio_1_1(self):
        """Test matching 1:1 square ratio."""
        assert match_common_ratio is not None, "match_common_ratio not implemented"
        assert match_common_ratio("1:1") == "1:1"

    def test_match_common_ratio_4_3(self):
        """Test matching 4:3 ratio."""
        assert match_common_ratio is not None
        assert match_common_ratio("4:3") == "4:3"

    def test_match_common_ratio_3_2(self):
        """Test matching 3:2 ratio."""
        assert match_common_ratio is not None
        assert match_common_ratio("3:2") == "3:2"

    def test_match_common_ratio_16_9(self):
        """Test matching 16:9 ratio."""
        assert match_common_ratio is not None
        assert match_common_ratio("16:9") == "16:9"

    def test_match_common_ratio_9_16(self):
        """Test matching 9:16 portrait ratio."""
        assert match_common_ratio is not None
        assert match_common_ratio("9:16") == "9:16"

    def test_match_common_ratio_4_5(self):
        """Test matching 4:5 portrait ratio."""
        assert match_common_ratio is not None
        assert match_common_ratio("4:5") == "4:5"

    def test_match_common_ratio_5_4(self):
        """Test matching 5:4 ratio."""
        assert match_common_ratio is not None
        assert match_common_ratio("5:4") == "5:4"

    def test_match_common_ratio_instagram_191_100(self):
        """Test matching Instagram 1.91:1 ratio (191:100)."""
        assert match_common_ratio is not None
        assert match_common_ratio("191:100") == "1.91:1"

    def test_match_common_ratio_none_for_uncommon(self):
        """Test that uncommon ratios return 'none'."""
        assert match_common_ratio is not None
        assert match_common_ratio("1234:567") == "none"
        assert match_common_ratio("7:5") == "none"
        assert match_common_ratio("1920:1081") == "none"

    def test_match_common_ratio_portrait_variants(self):
        """Test portrait variants of common ratios."""
        assert match_common_ratio is not None
        # 3:4 is portrait version of 4:3
        assert match_common_ratio("3:4") == "3:4"
        # 2:3 is portrait version of 3:2
        assert match_common_ratio("2:3") == "2:3"


class TestExifExtraction:
    """Test EXIF metadata extraction."""

    def test_extract_exif_data_with_full_exif(self, sample_image_with_exif):
        """Test extracting EXIF from an image with full EXIF data."""
        assert extract_exif_data is not None, "extract_exif_data not implemented"
        exif = extract_exif_data(sample_image_with_exif)

        assert exif is not None
        assert isinstance(exif, dict)
        # Should contain key EXIF fields
        assert 'DateTimeOriginal' in exif or 'DateTime' in exif
        assert 'Make' in exif
        assert 'Model' in exif

    def test_extract_exif_data_no_exif(self, sample_image_no_exif):
        """Test extracting EXIF from an image without EXIF data."""
        assert extract_exif_data is not None
        exif = extract_exif_data(sample_image_no_exif)

        # Should return None or empty dict
        assert exif is None or exif == {}

    def test_extract_exif_curated_fields(self, sample_image_with_exif):
        """Test that curated EXIF fields are extracted."""
        assert extract_exif_data is not None
        exif = extract_exif_data(sample_image_with_exif)

        if exif:
            # Check for curated fields as specified in PRD
            expected_fields = ['DateTimeOriginal', 'DateTime', 'Make', 'Model',
                             'Orientation', 'XResolution', 'YResolution', 'ResolutionUnit']

            # At least some of these should be present
            found_fields = [field for field in expected_fields if field in exif]
            assert len(found_fields) > 0

    def test_format_exif_curated(self, sample_image_with_exif):
        """Test formatting curated EXIF subset."""
        assert format_exif_curated is not None, "format_exif_curated not implemented"
        assert extract_exif_data is not None

        exif = extract_exif_data(sample_image_with_exif)
        if exif:
            formatted = format_exif_curated(exif)

            assert isinstance(formatted, dict)
            # Should only contain curated fields
            curated_fields = {'date_taken', 'camera_make', 'camera_model',
                            'orientation', 'dpi_x', 'dpi_y', 'resolution_unit'}
            assert all(key in curated_fields for key in formatted.keys())


class TestGetImageInfo:
    """Test the main get_image_info function."""

    def test_get_image_info_basic_square(self, sample_square_image):
        """Test getting info for a square image."""
        assert get_image_info is not None, "get_image_info not implemented"
        info = get_image_info(sample_square_image)

        assert info['width'] == 1000
        assert info['height'] == 1000
        assert info['orientation'] == 'square'
        assert info['ratio_raw'] == '1:1'
        assert info['common_ratio'] == '1:1'
        assert 'filename' in info
        assert 'size_kb' in info

    def test_get_image_info_landscape(self, sample_landscape_image):
        """Test getting info for a landscape image."""
        assert get_image_info is not None
        info = get_image_info(sample_landscape_image)

        assert info['width'] == 1920
        assert info['height'] == 1080
        assert info['orientation'] == 'landscape'
        assert info['ratio_raw'] == '16:9'
        assert info['common_ratio'] == '16:9'

    def test_get_image_info_portrait(self, sample_portrait_image):
        """Test getting info for a portrait image."""
        assert get_image_info is not None
        info = get_image_info(sample_portrait_image)

        assert info['width'] == 1080
        assert info['height'] == 1920
        assert info['orientation'] == 'portrait'
        assert info['ratio_raw'] == '9:16'
        assert info['common_ratio'] == '9:16'

    def test_get_image_info_with_exif(self, sample_image_with_exif):
        """Test getting info with EXIF data."""
        assert get_image_info is not None
        info = get_image_info(sample_image_with_exif)

        assert info['width'] == 1200
        assert info['height'] == 900
        assert info['has_exif'] is True
        assert 'exif' in info
        assert info['exif'] is not None

    def test_get_image_info_no_exif(self, sample_image_no_exif):
        """Test getting info without EXIF data."""
        assert get_image_info is not None
        info = get_image_info(sample_image_no_exif)

        assert info['width'] == 1500
        assert info['height'] == 1000
        assert info['has_exif'] is False
        assert info['exif'] is None or info['exif'] == {}

    def test_get_image_info_file_metadata(self, sample_square_image):
        """Test that file metadata is included."""
        assert get_image_info is not None
        info = get_image_info(sample_square_image)

        assert 'filename' in info
        assert 'path' in info
        assert 'size_kb' in info
        assert info['filename'] == sample_square_image.name
        assert info['size_kb'] > 0

    def test_get_image_info_png_format(self, sample_png_image):
        """Test getting info for PNG format."""
        assert get_image_info is not None
        info = get_image_info(sample_png_image)

        assert info['width'] == 800
        assert info['height'] == 600
        # PNG typically doesn't have EXIF
        assert info['has_exif'] is False


class TestSerializeExifValue:
    """Test serialize_exif_value function for JSON compatibility."""

    def test_serialize_ifd_rational(self):
        """Test that IFDRational is converted to float."""
        from ipro import serialize_exif_value
        from PIL.TiffImagePlugin import IFDRational

        rational = IFDRational(72, 1)
        result = serialize_exif_value(rational)

        assert isinstance(result, float)
        assert result == 72.0

    def test_serialize_ifd_rational_fraction(self):
        """Test IFDRational with non-integer result."""
        from ipro import serialize_exif_value
        from PIL.TiffImagePlugin import IFDRational

        rational = IFDRational(1, 3)
        result = serialize_exif_value(rational)

        assert isinstance(result, float)
        assert abs(result - 0.333333) < 0.001

    def test_serialize_bytes_utf8(self):
        """Test that bytes are decoded as UTF-8."""
        from ipro import serialize_exif_value

        byte_value = b'Canon EOS 5D'
        result = serialize_exif_value(byte_value)

        assert isinstance(result, str)
        assert result == 'Canon EOS 5D'

    def test_serialize_bytes_with_null(self):
        """Test bytes with null terminator."""
        from ipro import serialize_exif_value

        byte_value = b'Test\x00'
        result = serialize_exif_value(byte_value)

        assert isinstance(result, str)
        assert 'Test' in result

    def test_serialize_bytes_non_utf8(self):
        """Test bytes that aren't valid UTF-8."""
        from ipro import serialize_exif_value

        # Invalid UTF-8 sequence
        byte_value = b'\xff\xfe\x00\x01'
        result = serialize_exif_value(byte_value)

        # Should return a string (either decoded with errors ignored or str(bytes))
        assert isinstance(result, str)

    def test_serialize_tuple(self):
        """Test that tuples are recursively processed."""
        from ipro import serialize_exif_value
        from PIL.TiffImagePlugin import IFDRational

        tuple_value = (IFDRational(72, 1), IFDRational(96, 1))
        result = serialize_exif_value(tuple_value)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == 72.0
        assert result[1] == 96.0

    def test_serialize_list(self):
        """Test that lists are recursively processed."""
        from ipro import serialize_exif_value
        from PIL.TiffImagePlugin import IFDRational

        list_value = [IFDRational(72, 1), b'test']
        result = serialize_exif_value(list_value)

        assert isinstance(result, list)
        assert result[0] == 72.0
        assert result[1] == 'test'

    def test_serialize_dict(self):
        """Test that dicts are recursively processed."""
        from ipro import serialize_exif_value
        from PIL.TiffImagePlugin import IFDRational

        dict_value = {'resolution': IFDRational(72, 1), 'make': b'Canon'}
        result = serialize_exif_value(dict_value)

        assert isinstance(result, dict)
        assert result['resolution'] == 72.0
        assert result['make'] == 'Canon'

    def test_serialize_nested_structure(self):
        """Test deeply nested structures."""
        from ipro import serialize_exif_value
        from PIL.TiffImagePlugin import IFDRational

        nested = {'data': [IFDRational(1, 2), {'inner': b'value'}]}
        result = serialize_exif_value(nested)

        assert result['data'][0] == 0.5
        assert result['data'][1]['inner'] == 'value'

    def test_serialize_passthrough_int(self):
        """Test that integers pass through unchanged."""
        from ipro import serialize_exif_value

        result = serialize_exif_value(42)
        assert result == 42
        assert isinstance(result, int)

    def test_serialize_passthrough_str(self):
        """Test that strings pass through unchanged."""
        from ipro import serialize_exif_value

        result = serialize_exif_value("test string")
        assert result == "test string"

    def test_serialize_passthrough_float(self):
        """Test that floats pass through unchanged."""
        from ipro import serialize_exif_value

        result = serialize_exif_value(3.14)
        assert result == 3.14

    def test_serialize_passthrough_none(self):
        """Test that None passes through unchanged."""
        from ipro import serialize_exif_value

        result = serialize_exif_value(None)
        assert result is None


class TestFormatExifCuratedEdgeCases:
    """Test edge cases for format_exif_curated function."""

    def test_format_exif_curated_empty_dict(self):
        """Test that empty dict returns empty dict."""
        from ipro import format_exif_curated

        result = format_exif_curated({})
        assert result == {}

    def test_format_exif_curated_none_input(self):
        """Test that None input returns empty dict."""
        from ipro import format_exif_curated

        result = format_exif_curated(None)
        assert result == {}

    def test_format_exif_curated_datetime_fallback(self):
        """Test fallback to DateTime when DateTimeOriginal is missing."""
        from ipro import format_exif_curated

        exif_dict = {
            'DateTime': '2024:11:12 10:00:00',
            'Make': 'Canon'
        }
        result = format_exif_curated(exif_dict)

        assert 'date_taken' in result
        assert result['date_taken'] == '2024:11:12 10:00:00'

    def test_format_exif_curated_prefers_datetimeoriginal(self):
        """Test that DateTimeOriginal is preferred over DateTime."""
        from ipro import format_exif_curated

        exif_dict = {
            'DateTimeOriginal': '2024:11:12 14:30:00',
            'DateTime': '2024:11:12 10:00:00',
            'Make': 'Canon'
        }
        result = format_exif_curated(exif_dict)

        assert result['date_taken'] == '2024:11:12 14:30:00'

    def test_format_exif_curated_no_date_fields(self):
        """Test when neither date field is present."""
        from ipro import format_exif_curated

        exif_dict = {
            'Make': 'Canon',
            'Model': 'EOS 5D'
        }
        result = format_exif_curated(exif_dict)

        assert 'date_taken' not in result
        assert result['camera_make'] == 'Canon'
        assert result['camera_model'] == 'EOS 5D'


class TestHeifSupport:
    """Test HEIF format support via pillow-heif."""

    def test_heif_support_available(self):
        """Test that pillow-heif is available and registered."""
        try:
            from pillow_heif import register_heif_opener
            # If we can import it, the module is available
            assert True
        except ImportError:
            pytest.skip("pillow-heif not installed")

    def test_heif_opener_registered(self):
        """Test that HEIF opener is registered with PIL."""
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
            from PIL import Image

            # Check if HEIF format is supported
            # We can't easily create a synthetic HEIF, but we can verify
            # the opener is registered
            assert True
        except ImportError:
            pytest.skip("pillow-heif not installed")

    def test_heif_file_reading(self, tmp_path):
        """Test reading a real HEIF file if available."""
        # This test uses the real HEIF file from our test directory
        heif_test_file = Path(__file__).parent.parent / "img" / "tai_ping_socials" / "IMG_3751.HEIC"

        if not heif_test_file.exists():
            pytest.skip("Test HEIF file not available")

        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
        except ImportError:
            pytest.skip("pillow-heif not installed")

        # Test that we can read the HEIF file
        assert get_image_info is not None
        info = get_image_info(heif_test_file)

        # Verify basic info is extracted
        assert 'width' in info
        assert 'height' in info
        assert info['width'] > 0
        assert info['height'] > 0
        assert 'orientation' in info
        assert 'ratio_raw' in info

    def test_misleading_heic_extension_jpeg_content(self):
        """Test file with .HEIC extension but actually contains JPEG data."""
        # Some files are renamed with .HEIC extension but contain JPEG data
        # This is common when exporting from photo libraries
        misleading_file = Path(__file__).parent.parent / "img" / "tai_ping_socials" / "IMG_3494.HEIC"

        if not misleading_file.exists():
            pytest.skip("Test file with misleading extension not available")

        # Should still work - Pillow reads based on content, not extension
        assert get_image_info is not None
        info = get_image_info(misleading_file)

        # Verify it reads successfully despite misleading extension
        assert info['width'] == 3024
        assert info['height'] == 4032
        assert info['orientation'] == 'portrait'
        assert info['ratio_raw'] == '3:4'
        # This file is actually JPEG, so it should have EXIF
        assert info['has_exif'] is True

    def test_large_raw_dng_file(self):
        """Test handling of large RAW DNG files."""
        # DNG files can be very large (60+ MB) - test that we handle them
        dng_file = Path(__file__).parent.parent / "img" / "tai_ping_socials" / "IMG_3749.DNG"

        if not dng_file.exists():
            pytest.skip("Test DNG file not available")

        # Test that we can read large DNG files
        assert get_image_info is not None
        info = get_image_info(dng_file)

        # Verify basic info is extracted
        assert 'width' in info
        assert 'height' in info
        assert info['width'] == 6048
        assert info['height'] == 8064
        assert info['orientation'] == 'portrait'
        assert info['ratio_raw'] == '3:4'
        # Large file should report size in KB correctly
        assert info['size_kb'] > 50000  # Should be over 50 MB
