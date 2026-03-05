"""CLI integration tests for ipro resize command."""

import pytest
import subprocess
import sys
from pathlib import Path
from PIL import Image


def run_ipro_resize(input_file, *args):
    """
    Run ipro resize command and return result.

    Args:
        input_file: Path to input image file (positional argument)
        *args: Additional CLI arguments

    Returns:
        tuple: (exit_code, stdout, stderr)
    """
    cmd = [sys.executable, 'ipro.py', 'resize', str(input_file)] + list(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    return result.returncode, result.stdout, result.stderr


class TestResizeCommandBasics:
    """Test basic resize command functionality."""

    def test_resize_command_exists(self):
        """Test that resize subcommand is recognized."""
        cmd = [sys.executable, 'ipro.py', 'resize', '--help']
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0
        assert 'resize' in result.stdout.lower()

    def test_resize_requires_file_argument(self):
        """Test that resize command requires positional file argument."""
        cmd = [sys.executable, 'ipro.py', 'resize', '--width', '300']
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode != 0
        assert 'required' in result.stderr.lower() or 'file' in result.stderr.lower()

    def test_resize_requires_width_or_height(self):
        """Test that resize requires either --width or --height."""
        from .fixtures import create_test_image_file

        # Create test image
        img_path = create_test_image_file(1200, 800, filename='test.jpg')

        cmd = [sys.executable, 'ipro.py', 'resize', str(img_path)]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 2
        assert 'must specify' in result.stderr.lower() or 'width' in result.stderr.lower()

    def test_resize_file_not_found(self, temp_dir):
        """Test error handling for non-existent file."""
        fake_file = temp_dir / 'does_not_exist.jpg'
        exit_code, stdout, stderr = run_ipro_resize(fake_file, '--width', '300')

        assert exit_code == 3
        assert 'not found' in stderr.lower()
        assert str(fake_file) in stderr


class TestResizeByWidth:
    """Test resizing by width."""

    def test_resize_single_width(self, temp_dir):
        """Test resizing to a single width."""
        from .fixtures import create_test_image_file

        img_path = create_test_image_file(1200, 800, directory=temp_dir, filename='test.jpg')
        output_dir = temp_dir / 'resized'

        exit_code, stdout, stderr = run_ipro_resize(
            img_path, '--width', '300', '--output', str(output_dir)
        )

        assert exit_code == 0
        assert 'test.jpg' in stdout
        assert '300x200' in stdout
        assert 'Successfully created 1 image' in stdout

        # Verify file was created
        output_file = output_dir / 'test.jpg'
        assert output_file.exists()

        # Verify dimensions
        with Image.open(output_file) as img:
            assert img.size == (300, 200)

    def test_resize_multiple_widths(self, temp_dir):
        """Test resizing to multiple widths."""
        from .fixtures import create_test_image_file

        img_path = create_test_image_file(1920, 1080, directory=temp_dir, filename='test.jpg')
        output_dir = temp_dir / 'resized'

        exit_code, stdout, stderr = run_ipro_resize(
            img_path, '--width', '300,600,900', '--output', str(output_dir)
        )

        assert exit_code == 0
        assert 'test_300.jpg' in stdout
        assert 'test_600.jpg' in stdout
        assert 'test_900.jpg' in stdout
        assert 'Successfully created 3 image' in stdout

        # Verify all files were created
        assert (output_dir / 'test_300.jpg').exists()
        assert (output_dir / 'test_600.jpg').exists()
        assert (output_dir / 'test_900.jpg').exists()


class TestResizeByHeight:
    """Test resizing by height."""

    def test_resize_single_height(self, temp_dir):
        """Test resizing to a single height."""
        from .fixtures import create_test_image_file

        img_path = create_test_image_file(1200, 800, directory=temp_dir, filename='test.jpg')
        output_dir = temp_dir / 'resized'

        exit_code, stdout, stderr = run_ipro_resize(
            img_path, '--height', '400', '--output', str(output_dir)
        )

        assert exit_code == 0
        assert 'test.jpg' in stdout
        assert '600x400' in stdout  # Maintains aspect ratio

        # Verify file and dimensions
        output_file = output_dir / 'test.jpg'
        assert output_file.exists()

        with Image.open(output_file) as img:
            assert img.size == (600, 400)

    def test_resize_multiple_heights(self, temp_dir):
        """Test resizing to multiple heights."""
        from .fixtures import create_test_image_file

        img_path = create_test_image_file(1600, 900, directory=temp_dir, filename='test.jpg')
        output_dir = temp_dir / 'resized'

        exit_code, stdout, stderr = run_ipro_resize(
            img_path, '--height', '300,600', '--output', str(output_dir)
        )

        assert exit_code == 0
        assert 'Successfully created 2 image' in stdout

        # Verify dimensions
        with Image.open(output_dir / 'test_300.jpg') as img:
            assert img.size[1] == 300  # Height is 300

        with Image.open(output_dir / 'test_600.jpg') as img:
            assert img.size[1] == 600  # Height is 600


class TestResizeValidation:
    """Test resize command validation."""

    def test_resize_width_and_height_mutually_exclusive(self, temp_dir):
        """Test that --width and --height cannot be used together."""
        from .fixtures import create_test_image_file

        img_path = create_test_image_file(1200, 800, directory=temp_dir, filename='test.jpg')

        exit_code, stdout, stderr = run_ipro_resize(
            img_path, '--width', '300', '--height', '400'
        )

        assert exit_code == 2
        assert 'cannot specify both' in stderr.lower()

    def test_resize_quality_validation_too_low(self, temp_dir):
        """Test quality validation for values < 1."""
        from .fixtures import create_test_image_file

        img_path = create_test_image_file(1200, 800, directory=temp_dir, filename='test.jpg')

        exit_code, stdout, stderr = run_ipro_resize(
            img_path, '--width', '300', '--quality', '0'
        )

        assert exit_code == 2
        assert 'quality must be between 1-100' in stderr.lower()

    def test_resize_quality_validation_too_high(self, temp_dir):
        """Test quality validation for values > 100."""
        from .fixtures import create_test_image_file

        img_path = create_test_image_file(1200, 800, directory=temp_dir, filename='test.jpg')

        exit_code, stdout, stderr = run_ipro_resize(
            img_path, '--width', '300', '--quality', '101'
        )

        assert exit_code == 2
        assert 'quality must be between 1-100' in stderr.lower()

    def test_resize_quality_valid_range(self, temp_dir):
        """Test that quality values within 1-100 are accepted."""
        from .fixtures import create_test_image_file

        img_path = create_test_image_file(1200, 800, directory=temp_dir, filename='test.jpg')
        output_dir = temp_dir / 'resized'

        # Test minimum
        exit_code, stdout, stderr = run_ipro_resize(
            img_path, '--width', '300', '--quality', '1', '--output', str(output_dir)
        )
        assert exit_code == 0

        # Test maximum
        exit_code, stdout, stderr = run_ipro_resize(
            img_path, '--width', '300', '--quality', '100', '--output', str(output_dir)
        )
        assert exit_code == 0

    def test_resize_non_jpeg_file(self, temp_dir):
        """Test that non-JPEG files are rejected."""
        from PIL import Image

        # Create PNG file
        img = Image.new('RGB', (800, 600), color=(255, 0, 0))
        png_file = temp_dir / 'test.png'
        img.save(png_file, 'PNG')

        exit_code, stdout, stderr = run_ipro_resize(
            png_file, '--width', '300'
        )

        assert exit_code == 1
        assert 'unsupported format' in stderr.lower()


class TestResizeUpscalingPrevention:
    """Test upscaling prevention."""

    def test_resize_skip_larger_sizes(self, temp_dir):
        """Test that sizes larger than original are skipped."""
        from .fixtures import create_test_image_file

        # Create small image
        img_path = create_test_image_file(800, 600, directory=temp_dir, filename='small.jpg')
        output_dir = temp_dir / 'resized'

        exit_code, stdout, stderr = run_ipro_resize(
            img_path, '--width', '400,800,1200', '--output', str(output_dir)
        )

        assert exit_code == 0
        # Should create 400px and 800px (800px equals original width, 1200px exceeds it)
        assert 'small_400.jpg' in stdout
        assert 'small_800.jpg' in stdout
        assert 'Skipped 1200px' in stdout
        assert 'only 800px wide' in stdout

    def test_resize_all_sizes_skipped(self, temp_dir):
        """Test when all sizes would require upscaling."""
        from .fixtures import create_test_image_file

        # Create very small image
        img_path = create_test_image_file(400, 300, directory=temp_dir, filename='tiny.jpg')
        output_dir = temp_dir / 'resized'

        exit_code, stdout, stderr = run_ipro_resize(
            img_path, '--width', '800,1200,1600', '--output', str(output_dir)
        )

        assert exit_code == 0
        assert 'No images created' in stdout or 'all sizes would require upscaling' in stdout.lower()


class TestResizeOutputHandling:
    """Test output directory and file handling."""

    def test_resize_default_output_directory(self, temp_dir):
        """Test that default output directory is output/ next to source file."""
        from .fixtures import create_test_image_file

        # Create image in a subdirectory to verify source-relative behavior
        src_dir = temp_dir / 'photos'
        src_dir.mkdir()
        img = Image.new('RGB', (1200, 800), color=(100, 150, 200))
        img_path = src_dir / 'test.jpg'
        img.save(img_path, 'JPEG', quality=90)

        # Run from a different directory (temp_dir, not src_dir)
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            cmd = [sys.executable, str(Path(old_cwd) / 'ipro.py'), 'resize',
                   str(img_path), '--width', '300']
            result = subprocess.run(cmd, capture_output=True, text=True)

            assert result.returncode == 0
            assert 'Output directory:' in result.stdout

            # Verify file was created in resized-300w/ next to source, not in cwd
            assert (src_dir / 'resized-300w' / 'test.jpg').exists()
        finally:
            os.chdir(old_cwd)

    def test_resize_custom_output_directory(self, temp_dir):
        """Test custom output directory."""
        from .fixtures import create_test_image_file

        img_path = create_test_image_file(1200, 800, directory=temp_dir, filename='test.jpg')
        output_dir = temp_dir / 'custom' / 'output'

        exit_code, stdout, stderr = run_ipro_resize(
            img_path, '--width', '300', '--output', str(output_dir)
        )

        assert exit_code == 0
        assert str(output_dir) in stdout

        # Verify file was created in custom directory
        assert (output_dir / 'test.jpg').exists()

    def test_resize_creates_output_directory(self, temp_dir):
        """Test that output directory is created if it doesn't exist."""
        from .fixtures import create_test_image_file

        img_path = create_test_image_file(1200, 800, directory=temp_dir, filename='test.jpg')
        output_dir = temp_dir / 'new' / 'nested' / 'dir'

        assert not output_dir.exists()

        exit_code, stdout, stderr = run_ipro_resize(
            img_path, '--width', '300', '--output', str(output_dir)
        )

        assert exit_code == 0
        assert output_dir.exists()
        assert (output_dir / 'test.jpg').exists()


class TestResizeExitCodes:
    """Test exit codes match specification."""

    def test_resize_success_exit_code(self, temp_dir):
        """Test successful resize returns 0."""
        from .fixtures import create_test_image_file

        img_path = create_test_image_file(1200, 800, directory=temp_dir, filename='test.jpg')

        exit_code, stdout, stderr = run_ipro_resize(img_path, '--width', '300')
        assert exit_code == 0

    def test_resize_file_not_found_exit_code(self, temp_dir):
        """Test file not found returns exit code 3."""
        fake_file = temp_dir / 'missing.jpg'
        exit_code, stdout, stderr = run_ipro_resize(fake_file, '--width', '300')
        assert exit_code == 3

    def test_resize_invalid_args_exit_code(self, temp_dir):
        """Test invalid arguments return exit code 2."""
        from .fixtures import create_test_image_file

        img_path = create_test_image_file(1200, 800, directory=temp_dir, filename='test.jpg')

        # Both width and height
        exit_code, stdout, stderr = run_ipro_resize(
            img_path, '--width', '300', '--height', '400'
        )
        assert exit_code == 2

    def test_resize_unsupported_format_exit_code(self, temp_dir):
        """Test unsupported format returns exit code 1."""
        from PIL import Image

        img = Image.new('RGB', (800, 600), color=(255, 0, 0))
        png_file = temp_dir / 'test.png'
        img.save(png_file, 'PNG')

        exit_code, stdout, stderr = run_ipro_resize(png_file, '--width', '300')
        assert exit_code == 1


class TestResizeOutputFormat:
    """Test resize command output format."""

    def test_resize_shows_processing_info(self, temp_dir):
        """Test that processing info is displayed."""
        from .fixtures import create_test_image_file

        img_path = create_test_image_file(1920, 1080, directory=temp_dir, filename='photo.jpg')
        output_dir = temp_dir / 'resized'

        exit_code, stdout, stderr = run_ipro_resize(
            img_path, '--width', '300', '--output', str(output_dir)
        )

        assert exit_code == 0
        assert 'Processing:' in stdout
        assert 'photo.jpg' in stdout
        assert '1920x1080' in stdout
        assert f'Output directory: {output_dir.resolve()}' in stdout

    def test_resize_shows_created_files(self, temp_dir):
        """Test that created files are listed."""
        from .fixtures import create_test_image_file

        img_path = create_test_image_file(1200, 800, directory=temp_dir, filename='test.jpg')
        output_dir = temp_dir / 'resized'

        exit_code, stdout, stderr = run_ipro_resize(
            img_path, '--width', '300,600', '--output', str(output_dir)
        )

        assert exit_code == 0
        assert '✓ Created: test_300.jpg' in stdout
        assert '300x200' in stdout
        assert 'KB' in stdout
        assert '✓ Created: test_600.jpg' in stdout
        assert '600x400' in stdout

    def test_resize_shows_summary(self, temp_dir):
        """Test that summary is displayed."""
        from .fixtures import create_test_image_file

        img_path = create_test_image_file(1200, 800, directory=temp_dir, filename='test.jpg')
        output_dir = temp_dir / 'resized'

        exit_code, stdout, stderr = run_ipro_resize(
            img_path, '--width', '300,600', '--output', str(output_dir)
        )

        assert exit_code == 0
        assert 'Successfully created 2 image(s) from test.jpg' in stdout

    def test_resize_outputs_to_stdout(self, temp_dir):
        """Test that normal output goes to stdout."""
        from .fixtures import create_test_image_file

        img_path = create_test_image_file(1200, 800, directory=temp_dir, filename='test.jpg')

        exit_code, stdout, stderr = run_ipro_resize(img_path, '--width', '300')

        assert exit_code == 0
        assert len(stdout) > 0
        # stderr should be empty or minimal
        assert len(stderr) == 0 or stderr.strip() == ''

    def test_resize_errors_to_stderr(self, temp_dir):
        """Test that errors go to stderr."""
        fake_file = temp_dir / 'missing.jpg'
        exit_code, stdout, stderr = run_ipro_resize(fake_file, '--width', '300')

        assert exit_code != 0
        assert len(stderr) > 0
        assert len(stdout) == 0 or stdout.strip() == ''
