"""CLI integration tests for ipro info command."""

import pytest
import subprocess
import json
import sys
from pathlib import Path


def run_ipro_info(filepath, *args):
    """
    Run ipro info command and return result.

    Args:
        filepath: Path to image file
        *args: Additional CLI arguments

    Returns:
        tuple: (exit_code, stdout, stderr)
    """
    cmd = [sys.executable, 'ipro.py', 'info', str(filepath)] + list(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    return result.returncode, result.stdout, result.stderr


class TestInfoCommandBasics:
    """Test basic info command functionality."""

    def test_info_command_exists(self):
        """Test that info subcommand is recognized."""
        cmd = [sys.executable, 'ipro.py', 'info', '--help']
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        # Should not fail and should mention 'info'
        assert result.returncode == 0
        assert 'info' in result.stdout.lower()

    def test_info_requires_file_argument(self):
        """Test that info command requires a file argument."""
        cmd = [sys.executable, 'ipro.py', 'info']
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        # Should fail with non-zero exit code
        assert result.returncode != 0
        # Error should mention missing argument
        assert 'required' in result.stderr.lower() or 'required' in result.stdout.lower()

    def test_info_file_not_found(self, temp_dir):
        """Test error handling for non-existent file."""
        fake_file = temp_dir / 'does_not_exist.jpg'
        exit_code, stdout, stderr = run_ipro_info(fake_file)

        # Should exit with code 3 (file not found)
        assert exit_code == 3
        # Error should go to stderr
        assert 'not found' in stderr.lower()
        assert str(fake_file) in stderr

    def test_info_unsupported_file_format(self, sample_non_image_file):
        """Test error handling for non-image file."""
        exit_code, stdout, stderr = run_ipro_info(sample_non_image_file)

        # Should exit with non-zero code
        assert exit_code != 0
        # Error should mention unsupported format
        assert 'unsupported' in stderr.lower() or 'cannot' in stderr.lower()


class TestInfoDefaultOutput:
    """Test default human-readable output format."""

    def test_info_default_output_square(self, sample_square_image):
        """Test default output for square image."""
        exit_code, stdout, stderr = run_ipro_info(sample_square_image)

        assert exit_code == 0
        # Output should be on stdout
        assert len(stdout) > 0
        # Should contain key information
        assert '1000' in stdout  # dimensions
        assert '1:1' in stdout  # aspect ratio
        assert 'square' in stdout.lower()  # orientation
        assert sample_square_image.name in stdout  # filename

    def test_info_default_output_landscape(self, sample_landscape_image):
        """Test default output for landscape image."""
        exit_code, stdout, stderr = run_ipro_info(sample_landscape_image)

        assert exit_code == 0
        assert '1920' in stdout and '1080' in stdout
        assert '16:9' in stdout
        assert 'landscape' in stdout.lower()

    def test_info_default_output_portrait(self, sample_portrait_image):
        """Test default output for portrait image."""
        exit_code, stdout, stderr = run_ipro_info(sample_portrait_image)

        assert exit_code == 0
        assert '1080' in stdout and '1920' in stdout
        assert '9:16' in stdout
        assert 'portrait' in stdout.lower()

    def test_info_default_shows_file_size(self, sample_square_image):
        """Test that default output includes file size."""
        exit_code, stdout, stderr = run_ipro_info(sample_square_image)

        assert exit_code == 0
        # Should mention KB or file size
        assert 'kb' in stdout.lower() or 'size' in stdout.lower()

    def test_info_default_shows_exif_presence(self, sample_image_with_exif):
        """Test that default output indicates EXIF presence."""
        exit_code, stdout, stderr = run_ipro_info(sample_image_with_exif)

        assert exit_code == 0
        # Should mention EXIF in some way
        assert 'exif' in stdout.lower()


class TestInfoJsonOutput:
    """Test JSON output format."""

    def test_info_json_flag(self, sample_square_image):
        """Test --json flag produces valid JSON."""
        exit_code, stdout, stderr = run_ipro_info(sample_square_image, '--json')

        assert exit_code == 0
        # Should be valid JSON
        data = json.loads(stdout)
        assert isinstance(data, dict)

    def test_info_json_contains_required_fields(self, sample_square_image):
        """Test JSON output contains all required fields."""
        exit_code, stdout, stderr = run_ipro_info(sample_square_image, '--json')

        assert exit_code == 0
        data = json.loads(stdout)

        # Required fields from PRD
        required_fields = [
            'filename', 'path', 'width', 'height',
            'orientation', 'ratio_raw', 'common_ratio',
            'size_kb', 'has_exif'
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_info_json_correct_values_square(self, sample_square_image):
        """Test JSON output has correct values for square image."""
        exit_code, stdout, stderr = run_ipro_info(sample_square_image, '--json')

        assert exit_code == 0
        data = json.loads(stdout)

        assert data['width'] == 1000
        assert data['height'] == 1000
        assert data['orientation'] == 'square'
        assert data['ratio_raw'] == '1:1'
        assert data['common_ratio'] == '1:1'
        assert data['filename'] == sample_square_image.name
        assert data['size_kb'] > 0

    def test_info_json_correct_values_landscape(self, sample_landscape_image):
        """Test JSON output for landscape image."""
        exit_code, stdout, stderr = run_ipro_info(sample_landscape_image, '--json')

        assert exit_code == 0
        data = json.loads(stdout)

        assert data['width'] == 1920
        assert data['height'] == 1080
        assert data['orientation'] == 'landscape'
        assert data['ratio_raw'] == '16:9'
        assert data['common_ratio'] == '16:9'

    def test_info_json_with_exif(self, sample_image_with_exif):
        """Test JSON output includes EXIF data when present."""
        exit_code, stdout, stderr = run_ipro_info(sample_image_with_exif, '--json')

        assert exit_code == 0
        data = json.loads(stdout)

        assert data['has_exif'] is True
        assert 'exif' in data
        # Should have curated EXIF fields
        assert data['exif'] is not None

    def test_info_json_without_exif(self, sample_image_no_exif):
        """Test JSON output when no EXIF data present."""
        exit_code, stdout, stderr = run_ipro_info(sample_image_no_exif, '--json')

        assert exit_code == 0
        data = json.loads(stdout)

        assert data['has_exif'] is False


class TestInfoShortOutput:
    """Test CSV short output format."""

    def test_info_short_flag(self, sample_square_image):
        """Test --short flag produces CSV line."""
        exit_code, stdout, stderr = run_ipro_info(sample_square_image, '--short')

        assert exit_code == 0
        # Should be a single line with commas
        lines = stdout.strip().split('\n')
        assert len(lines) == 1
        assert ',' in stdout

    def test_info_short_field_count(self, sample_square_image):
        """Test --short output has correct number of fields."""
        exit_code, stdout, stderr = run_ipro_info(sample_square_image, '--short')

        assert exit_code == 0
        fields = stdout.strip().split(',')

        # From PRD: filename,width,height,orientation,ratio_raw,common_ratio,size_kb,creation_date
        # That's 8 fields minimum
        assert len(fields) >= 8

    def test_info_short_correct_values(self, sample_square_image):
        """Test --short output has correct values in correct order."""
        exit_code, stdout, stderr = run_ipro_info(sample_square_image, '--short')

        assert exit_code == 0
        fields = stdout.strip().split(',')

        # Expected order: filename,format,frames,width,height,orientation,ratio_raw,common_ratio,size_kb,creation_date
        assert fields[0] == sample_square_image.name  # filename
        assert fields[1] == 'JPEG'  # format
        assert fields[2] == '1'  # frames
        assert fields[3] == '1000'  # width
        assert fields[4] == '1000'  # height
        assert fields[5] == 'square'  # orientation
        assert fields[6] == '1:1'  # ratio_raw
        assert fields[7] == '1:1'  # common_ratio
        # fields[8] should be size_kb (number)
        assert float(fields[8]) > 0

    def test_info_short_landscape(self, sample_landscape_image):
        """Test --short output for landscape image."""
        exit_code, stdout, stderr = run_ipro_info(sample_landscape_image, '--short')

        assert exit_code == 0
        fields = stdout.strip().split(',')

        assert fields[1] == 'JPEG'  # format
        assert fields[2] == '1'  # frames
        assert fields[3] == '1920'  # width
        assert fields[4] == '1080'  # height
        assert fields[5] == 'landscape'  # orientation
        assert fields[6] == '16:9'  # ratio_raw
        assert fields[7] == '16:9'  # common_ratio

    def test_info_short_batch_compatible(self, sample_square_image, sample_landscape_image):
        """Test that multiple --short calls can be batched for CSV."""
        exit_code1, stdout1, stderr1 = run_ipro_info(sample_square_image, '--short')
        exit_code2, stdout2, stderr2 = run_ipro_info(sample_landscape_image, '--short')

        assert exit_code1 == 0 and exit_code2 == 0

        # Should be able to concatenate these into a CSV
        csv_lines = [stdout1.strip(), stdout2.strip()]
        assert len(csv_lines) == 2
        # Each should have the same number of fields
        fields1 = csv_lines[0].split(',')
        fields2 = csv_lines[1].split(',')
        assert len(fields1) == len(fields2)


class TestInfoExifFlags:
    """Test EXIF-related flags."""

    def test_info_exif_flag_shows_curated(self, sample_image_with_exif):
        """Test --exif flag shows curated EXIF data."""
        exit_code, stdout, stderr = run_ipro_info(sample_image_with_exif, '--exif')

        assert exit_code == 0
        # Should show EXIF information
        assert 'exif' in stdout.lower() or 'camera' in stdout.lower() or 'date' in stdout.lower()

    def test_info_exif_all_flag(self, sample_image_with_exif):
        """Test --exif-all flag shows all EXIF tags."""
        exit_code, stdout, stderr = run_ipro_info(sample_image_with_exif, '--exif-all')

        assert exit_code == 0
        # Should show more detailed EXIF information
        # The output should be longer than the curated version
        assert len(stdout) > 0

    def test_info_exif_json_combination(self, sample_image_with_exif):
        """Test --json with --exif-all includes full EXIF."""
        exit_code, stdout, stderr = run_ipro_info(
            sample_image_with_exif, '--json', '--exif-all'
        )

        assert exit_code == 0
        data = json.loads(stdout)

        # Should have exif field with all tags
        assert 'exif' in data
        assert data['exif'] is not None
        # When --exif-all is used, should have more fields
        assert len(data['exif']) > 0


class TestInfoExitCodes:
    """Test exit codes match PRD specification."""

    def test_info_success_exit_code(self, sample_square_image):
        """Test successful info command returns 0."""
        exit_code, stdout, stderr = run_ipro_info(sample_square_image)
        assert exit_code == 0

    def test_info_file_not_found_exit_code(self, temp_dir):
        """Test file not found returns exit code 3."""
        fake_file = temp_dir / 'missing.jpg'
        exit_code, stdout, stderr = run_ipro_info(fake_file)
        assert exit_code == 3

    def test_info_unsupported_format_exit_code(self, sample_non_image_file):
        """Test unsupported format returns non-zero exit code."""
        exit_code, stdout, stderr = run_ipro_info(sample_non_image_file)
        # Should be non-zero (could be 1 or 4 depending on error type)
        assert exit_code != 0

    def test_info_missing_argument_exit_code(self):
        """Test missing file argument returns exit code 2."""
        cmd = [sys.executable, 'ipro.py', 'info']
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        # Invalid arguments should return code 2
        assert result.returncode == 2


class TestInfoFormatSupport:
    """Test that info supports various image formats."""

    def test_info_supports_png(self, sample_png_image):
        """Test info command works with PNG files."""
        exit_code, stdout, stderr = run_ipro_info(sample_png_image)

        assert exit_code == 0
        assert '800' in stdout and '600' in stdout

    def test_info_supports_jpeg(self, sample_square_image):
        """Test info command works with JPEG files."""
        exit_code, stdout, stderr = run_ipro_info(sample_square_image)

        assert exit_code == 0
        assert '1000' in stdout


class TestInfoEdgeCases:
    """Test edge cases and special scenarios."""

    def test_info_with_spaces_in_filename(self, temp_dir):
        """Test handling of filenames with spaces."""
        from .fixtures import create_test_image_file

        filepath = create_test_image_file(
            800, 600,
            directory=temp_dir,
            filename='image with spaces.jpg'
        )

        exit_code, stdout, stderr = run_ipro_info(filepath)

        assert exit_code == 0
        assert 'image with spaces.jpg' in stdout

    def test_info_outputs_to_stdout_not_stderr(self, sample_square_image):
        """Test that normal output goes to stdout, not stderr."""
        exit_code, stdout, stderr = run_ipro_info(sample_square_image)

        assert exit_code == 0
        # Normal output should be on stdout
        assert len(stdout) > 0
        # stderr should be empty or minimal
        assert len(stderr) == 0 or stderr.strip() == ''

    def test_info_errors_to_stderr(self, temp_dir):
        """Test that errors go to stderr, not stdout."""
        fake_file = temp_dir / 'missing.jpg'
        exit_code, stdout, stderr = run_ipro_info(fake_file)

        assert exit_code != 0
        # Error should be on stderr
        assert len(stderr) > 0
        # stdout should be empty
        assert len(stdout) == 0 or stdout.strip() == ''

    def test_info_uncommon_aspect_ratio(self, temp_dir):
        """Test image with uncommon aspect ratio shows 'none' for common_ratio."""
        from .fixtures import create_test_image_file

        # Create image with weird dimensions
        filepath = create_test_image_file(
            1234, 567,
            directory=temp_dir,
            filename='weird_ratio.jpg'
        )

        exit_code, stdout, stderr = run_ipro_info(filepath, '--json')

        assert exit_code == 0
        data = json.loads(stdout)

        assert data['ratio_raw'] == '1234:567'
        assert data['common_ratio'] == 'none'

    def test_info_heif_format(self):
        """Test that HEIF files can be processed if pillow-heif is installed."""
        # This test uses the real HEIF file from our test directory
        from pathlib import Path
        heif_test_file = Path(__file__).parent.parent / "img" / "tai_ping_socials" / "IMG_3751.HEIC"

        if not heif_test_file.exists():
            pytest.skip("Test HEIF file not available")

        try:
            from pillow_heif import register_heif_opener
        except ImportError:
            pytest.skip("pillow-heif not installed")

        # Test default output
        exit_code, stdout, stderr = run_ipro_info(heif_test_file)

        assert exit_code == 0
        assert 'IMG_3751.HEIC' in stdout
        assert 'portrait' in stdout.lower() or 'Portrait' in stdout
        assert '3:4' in stdout

        # Test JSON output
        exit_code, stdout, stderr = run_ipro_info(heif_test_file, '--json')

        assert exit_code == 0
        data = json.loads(stdout)
        assert data['filename'] == 'IMG_3751.HEIC'
        assert data['width'] == 3024
        assert data['height'] == 4032
        assert data['orientation'] == 'portrait'
        assert data['ratio_raw'] == '3:4'

        # Test CSV output
        exit_code, stdout, stderr = run_ipro_info(heif_test_file, '--short')

        assert exit_code == 0
        assert 'IMG_3751.HEIC' in stdout
        assert '3024' in stdout
        assert '4032' in stdout
