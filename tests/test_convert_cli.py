"""CLI integration tests for ipro convert command."""

import pytest
import subprocess
import sys
from pathlib import Path
from PIL import Image


def run_ipro_convert(filepath, *args):
    """
    Run ipro convert command and return result.

    Args:
        filepath: Path to image file
        *args: Additional CLI arguments

    Returns:
        tuple: (exit_code, stdout, stderr)
    """
    cmd = [sys.executable, 'ipro.py', 'convert', str(filepath)] + list(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    return result.returncode, result.stdout, result.stderr


class TestConvertCommandBasics:
    """Test basic convert command functionality."""

    def test_convert_command_exists(self):
        """Test that convert subcommand is recognized."""
        cmd = [sys.executable, 'ipro.py', 'convert', '--help']
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0
        assert 'convert' in result.stdout.lower()

    def test_convert_requires_file_argument(self):
        """Test that convert command requires a file argument."""
        cmd = [sys.executable, 'ipro.py', 'convert', '--format', 'jpeg']
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode != 0

    def test_convert_requires_format_option(self, sample_square_image):
        """Test that convert requires --format option."""
        exit_code, stdout, stderr = run_ipro_convert(sample_square_image)
        assert exit_code != 0
        assert 'format' in stderr.lower() or 'required' in stderr.lower()

    def test_convert_file_not_found(self, temp_dir):
        """Test error handling for non-existent file."""
        fake_file = temp_dir / 'does_not_exist.jpg'
        exit_code, stdout, stderr = run_ipro_convert(
            fake_file, '--format', 'png'
        )
        assert exit_code == 3
        assert 'not found' in stderr.lower()

    def test_convert_unsupported_file(self, sample_non_image_file):
        """Test error handling for non-image file."""
        exit_code, stdout, stderr = run_ipro_convert(
            sample_non_image_file, '--format', 'png'
        )
        assert exit_code == 4


class TestConvertFormatOption:
    """Test --format option."""

    def test_convert_to_png(self, sample_square_image, temp_dir):
        """Test converting to PNG format."""
        output_dir = temp_dir / "converted"
        exit_code, stdout, stderr = run_ipro_convert(
            sample_square_image, '--format', 'png', '--output', str(output_dir)
        )

        assert exit_code == 0
        # Check output file exists
        expected_output = output_dir / "square.png"
        assert expected_output.exists()
        # Verify format
        with Image.open(expected_output) as img:
            assert img.format == "PNG"

    def test_convert_to_jpeg(self, sample_png_image, temp_dir):
        """Test converting to JPEG format."""
        output_dir = temp_dir / "converted"
        exit_code, stdout, stderr = run_ipro_convert(
            sample_png_image, '--format', 'jpeg', '--output', str(output_dir)
        )

        assert exit_code == 0
        expected_output = output_dir / "test.jpg"
        assert expected_output.exists()
        with Image.open(expected_output) as img:
            assert img.format == "JPEG"

    def test_convert_jpg_alias(self, sample_png_image, temp_dir):
        """Test that 'jpg' works as format alias."""
        output_dir = temp_dir / "converted"
        exit_code, stdout, stderr = run_ipro_convert(
            sample_png_image, '--format', 'jpg', '--output', str(output_dir)
        )

        assert exit_code == 0
        expected_output = output_dir / "test.jpg"
        assert expected_output.exists()

    def test_convert_to_webp(self, sample_square_image, temp_dir):
        """Test converting to WebP format."""
        output_dir = temp_dir / "converted"
        exit_code, stdout, stderr = run_ipro_convert(
            sample_square_image, '--format', 'webp', '--output', str(output_dir)
        )

        assert exit_code == 0
        expected_output = output_dir / "square.webp"
        assert expected_output.exists()
        with Image.open(expected_output) as img:
            assert img.format == "WEBP"

    def test_convert_to_webp_with_quality(self, sample_png_image, temp_dir):
        """Test converting to WebP with quality option."""
        output_dir = temp_dir / "converted"
        exit_code, stdout, stderr = run_ipro_convert(
            sample_png_image, '--format', 'webp', '--quality', '85',
            '--output', str(output_dir)
        )

        assert exit_code == 0
        expected_output = output_dir / "test.webp"
        assert expected_output.exists()

    def test_convert_unsupported_target_format(self, sample_square_image):
        """Test error for unsupported target format."""
        exit_code, stdout, stderr = run_ipro_convert(
            sample_square_image, '--format', 'xyz'
        )
        assert exit_code != 0
        assert 'unsupported' in stderr.lower() or 'format' in stderr.lower()

    def test_convert_uppercase_format(self, sample_png_image, temp_dir):
        """Test that uppercase format names work."""
        output_dir = temp_dir / "converted"
        exit_code, stdout, stderr = run_ipro_convert(
            sample_png_image, '--format', 'JPEG', '--output', str(output_dir)
        )

        assert exit_code == 0
        expected_output = output_dir / "test.jpg"
        assert expected_output.exists()


class TestConvertOutputDirectory:
    """Test output directory handling."""

    def test_default_output_directory(self, sample_square_image):
        """Test that default output is output/ next to source file."""
        # Run from temp dir to avoid polluting project
        import tempfile
        import shutil

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create source in a subdirectory to verify source-relative behavior
            src_dir = Path(tmpdir) / "photos"
            src_dir.mkdir()
            src = src_dir / "test.jpg"
            shutil.copy(sample_square_image, src)

            cmd = [sys.executable, str(Path(__file__).parent.parent / 'ipro.py'),
                   'convert', str(src), '--format', 'png']
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=tmpdir)

            assert result.returncode == 0
            # Output should be next to source file, not in cwd
            expected = src_dir / "converted" / "test.png"
            assert expected.exists()

    def test_custom_output_directory(self, sample_square_image, temp_dir):
        """Test --output option specifies custom directory."""
        output_dir = temp_dir / "my_output"

        exit_code, stdout, stderr = run_ipro_convert(
            sample_square_image, '--format', 'png', '--output', str(output_dir)
        )

        assert exit_code == 0
        assert output_dir.exists()
        assert (output_dir / "square.png").exists()

    def test_output_directory_created_if_missing(self, sample_square_image, temp_dir):
        """Test that output directory is created if it doesn't exist."""
        output_dir = temp_dir / "new_dir" / "nested"
        assert not output_dir.exists()

        exit_code, stdout, stderr = run_ipro_convert(
            sample_square_image, '--format', 'png', '--output', str(output_dir)
        )

        assert exit_code == 0
        assert output_dir.exists()


class TestConvertQualityOption:
    """Test --quality option."""

    def test_quality_option_jpeg(self, sample_png_image, temp_dir):
        """Test quality option for JPEG output."""
        output_dir = temp_dir / "converted"

        exit_code, stdout, stderr = run_ipro_convert(
            sample_png_image, '--format', 'jpeg', '--quality', '75',
            '--output', str(output_dir)
        )

        assert exit_code == 0
        expected_output = output_dir / "test.jpg"
        assert expected_output.exists()

    def test_quality_invalid_value(self, sample_square_image):
        """Test error for invalid quality value."""
        exit_code, stdout, stderr = run_ipro_convert(
            sample_square_image, '--format', 'jpeg', '--quality', '150'
        )
        assert exit_code == 2
        assert 'quality' in stderr.lower() or '1-100' in stderr.lower()

    def test_quality_zero_invalid(self, sample_square_image):
        """Test error for quality value of 0."""
        exit_code, stdout, stderr = run_ipro_convert(
            sample_square_image, '--format', 'jpeg', '--quality', '0'
        )
        assert exit_code == 2


class TestConvertStripExif:
    """Test --strip-exif option."""

    def test_strip_exif_removes_metadata(self, sample_image_with_exif, temp_dir):
        """Test that --strip-exif removes EXIF data."""
        output_dir = temp_dir / "converted"

        exit_code, stdout, stderr = run_ipro_convert(
            sample_image_with_exif, '--format', 'jpeg', '--strip-exif',
            '--output', str(output_dir)
        )

        assert exit_code == 0
        output_file = output_dir / "with_exif.jpg"
        assert output_file.exists()

        with Image.open(output_file) as img:
            exif = img.getexif()
            assert not exif or len(exif) == 0

    def test_exif_preserved_by_default(self, sample_image_with_exif, temp_dir):
        """Test that EXIF is preserved when --strip-exif not used."""
        output_dir = temp_dir / "converted"

        exit_code, stdout, stderr = run_ipro_convert(
            sample_image_with_exif, '--format', 'jpeg',
            '--output', str(output_dir)
        )

        assert exit_code == 0
        output_file = output_dir / "with_exif.jpg"

        with Image.open(output_file) as img:
            exif = img.getexif()
            assert exif and len(exif) > 0


class TestConvertExitCodes:
    """Test exit codes for various scenarios."""

    def test_success_exit_code(self, sample_square_image, temp_dir):
        """Test successful conversion returns exit code 0."""
        output_dir = temp_dir / "converted"
        exit_code, _, _ = run_ipro_convert(
            sample_square_image, '--format', 'png', '--output', str(output_dir)
        )
        assert exit_code == 0

    def test_file_not_found_exit_code(self, temp_dir):
        """Test file not found returns exit code 3."""
        exit_code, _, _ = run_ipro_convert(
            temp_dir / "nonexistent.jpg", '--format', 'png'
        )
        assert exit_code == 3

    def test_cannot_read_exit_code(self, sample_non_image_file):
        """Test unreadable file returns exit code 4."""
        exit_code, _, _ = run_ipro_convert(
            sample_non_image_file, '--format', 'png'
        )
        assert exit_code == 4

    def test_invalid_args_exit_code(self, sample_square_image):
        """Test invalid arguments returns exit code 2."""
        exit_code, _, _ = run_ipro_convert(
            sample_square_image, '--format', 'jpeg', '--quality', '999'
        )
        assert exit_code == 2


class TestConvertOutputMessages:
    """Test output messages."""

    def test_success_message(self, sample_square_image, temp_dir):
        """Test success message is printed."""
        output_dir = temp_dir / "converted"
        exit_code, stdout, stderr = run_ipro_convert(
            sample_square_image, '--format', 'png', '--output', str(output_dir)
        )

        assert exit_code == 0
        combined = stdout + stderr
        assert 'square.png' in combined or 'created' in combined.lower()

    def test_overwrite_warning(self, sample_square_image, temp_dir):
        """Test warning when overwriting existing file."""
        output_dir = temp_dir / "converted"
        output_dir.mkdir(parents=True)

        # Create existing file
        existing = output_dir / "square.png"
        existing.write_text("existing")

        exit_code, stdout, stderr = run_ipro_convert(
            sample_square_image, '--format', 'png', '--output', str(output_dir)
        )

        assert exit_code == 0
        # File should be overwritten
        assert existing.exists()
        # Should be actual image now
        with Image.open(existing) as img:
            assert img.format == "PNG"


class TestConvertEdgeCases:
    """Test edge cases and special scenarios."""

    def test_same_format_conversion(self, sample_square_image, temp_dir):
        """Test converting JPEG to JPEG (re-encoding)."""
        output_dir = temp_dir / "converted"

        exit_code, stdout, stderr = run_ipro_convert(
            sample_square_image, '--format', 'jpeg', '--output', str(output_dir)
        )

        assert exit_code == 0
        expected = output_dir / "square.jpg"
        assert expected.exists()

    def test_filename_with_spaces(self, temp_dir):
        """Test handling filenames with spaces."""
        img = Image.new('RGB', (100, 100), (255, 0, 0))
        original = temp_dir / "my photo.jpg"
        img.save(original, 'JPEG')

        output_dir = temp_dir / "converted"
        exit_code, stdout, stderr = run_ipro_convert(
            original, '--format', 'png', '--output', str(output_dir)
        )

        assert exit_code == 0
        expected = output_dir / "my photo.png"
        assert expected.exists()

    def test_unicode_filename(self, temp_dir):
        """Test handling unicode in filenames."""
        img = Image.new('RGB', (100, 100), (255, 0, 0))
        original = temp_dir / "фото.jpg"  # Russian "photo"
        img.save(original, 'JPEG')

        output_dir = temp_dir / "converted"
        exit_code, stdout, stderr = run_ipro_convert(
            original, '--format', 'png', '--output', str(output_dir)
        )

        assert exit_code == 0
        expected = output_dir / "фото.png"
        assert expected.exists()

    def test_preserves_original_file(self, sample_square_image, temp_dir):
        """Test that original file is preserved (non-destructive)."""
        original_exists_before = sample_square_image.exists()
        output_dir = temp_dir / "converted"

        run_ipro_convert(
            sample_square_image, '--format', 'png', '--output', str(output_dir)
        )

        assert original_exists_before
        assert sample_square_image.exists()
