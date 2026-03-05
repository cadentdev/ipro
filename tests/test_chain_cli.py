"""CLI integration tests for command chaining with '+' separator."""
import subprocess
import sys
import pytest
from pathlib import Path


IMGPRO = str(Path(__file__).parent.parent / 'ipro.py')


def run_ipro(*args):
    """Run ipro.py with the given arguments and return CompletedProcess."""
    return subprocess.run(
        [sys.executable, IMGPRO] + list(args),
        capture_output=True,
        text=True,
    )


class TestChainResizeConvert:
    """Tests for chaining resize + convert commands."""

    def test_resize_then_convert_to_webp(self, sample_landscape_image, temp_dir):
        """resize + convert: produces resized WebP files."""
        output_resize = temp_dir / 'resized'
        output_convert = temp_dir / 'converted'

        result = run_ipro(
            'resize', str(sample_landscape_image),
            '--width', '300',
            '--output', str(output_resize),
            '+',
            'convert', '--format', 'webp',
            '--output', str(output_convert),
        )

        assert result.returncode == 0
        # Resize should have created one file
        resized_files = list(output_resize.glob('*.jpg'))
        assert len(resized_files) == 1
        # Convert should have created one WebP file
        converted_files = list(output_convert.glob('*.webp'))
        assert len(converted_files) == 1
        assert converted_files[0].stem == 'landscape'

    def test_resize_multiple_then_convert(self, sample_landscape_image, temp_dir):
        """resize with multiple widths + convert: converts each resized file."""
        output_resize = temp_dir / 'resized'
        output_convert = temp_dir / 'converted'

        result = run_ipro(
            'resize', str(sample_landscape_image),
            '--width', '300,600',
            '--output', str(output_resize),
            '+',
            'convert', '--format', 'png',
            '--output', str(output_convert),
        )

        assert result.returncode == 0
        # Two resized JPEGs
        resized_files = sorted(output_resize.glob('*.jpg'))
        assert len(resized_files) == 2
        # Two converted PNGs
        converted_files = sorted(output_convert.glob('*.png'))
        assert len(converted_files) == 2
        stems = {f.stem for f in converted_files}
        assert stems == {'landscape_300', 'landscape_600'}

    def test_resize_then_convert_with_quality(self, sample_landscape_image, temp_dir):
        """resize + convert with custom quality."""
        output_resize = temp_dir / 'resized'
        output_convert = temp_dir / 'converted'

        result = run_ipro(
            'resize', str(sample_landscape_image),
            '--width', '300',
            '--quality', '50',
            '--output', str(output_resize),
            '+',
            'convert', '--format', 'webp',
            '--quality', '60',
            '--output', str(output_convert),
        )

        assert result.returncode == 0
        converted_files = list(output_convert.glob('*.webp'))
        assert len(converted_files) == 1


class TestChainConvertResize:
    """Tests for chaining convert + resize (convert first, then resize)."""

    def test_convert_png_then_resize(self, sample_landscape_image, temp_dir):
        """convert to PNG + resize: converts first, but resize fails on non-JPEG.
        This tests the error propagation behavior."""
        output_convert = temp_dir / 'converted'
        output_resize = temp_dir / 'resized'

        result = run_ipro(
            'convert', str(sample_landscape_image),
            '--format', 'png',
            '--output', str(output_convert),
            '+',
            'resize', '--width', '300',
            '--output', str(output_resize),
        )

        # Resize only supports JPEG, so this should fail at the resize step
        assert result.returncode == 1  # unsupported format
        # But the convert step should still have produced a file
        converted_files = list(output_convert.glob('*.png'))
        assert len(converted_files) == 1

    def test_convert_jpeg_then_resize(self, sample_png_image, temp_dir):
        """convert PNG to JPEG + resize: should work end to end."""
        output_convert = temp_dir / 'converted'
        output_resize = temp_dir / 'resized'

        result = run_ipro(
            'convert', str(sample_png_image),
            '--format', 'jpeg',
            '--output', str(output_convert),
            '+',
            'resize', '--width', '300',
            '--output', str(output_resize),
        )

        assert result.returncode == 0
        converted_files = list(output_convert.glob('*.jpg'))
        assert len(converted_files) == 1
        resized_files = list(output_resize.glob('*.jpg'))
        assert len(resized_files) == 1


class TestChainThreeCommands:
    """Tests for chaining three commands together."""

    def test_resize_convert_rename(self, sample_landscape_image, temp_dir):
        """resize + convert + rename --ext: three-step chain."""
        output_resize = temp_dir / 'resized'
        output_convert = temp_dir / 'converted'
        output_rename = temp_dir / 'renamed'

        result = run_ipro(
            'resize', str(sample_landscape_image),
            '--width', '300',
            '--output', str(output_resize),
            '+',
            'convert', '--format', 'webp',
            '--output', str(output_convert),
            '+',
            'rename', '--ext',
            '--output', str(output_rename),
        )

        assert result.returncode == 0
        # Final step should have produced renamed file(s)
        renamed_files = list(output_rename.iterdir())
        assert len(renamed_files) == 1
        # Should have .webp extension (actual format is webp)
        assert renamed_files[0].suffix == '.webp'


class TestChainWithInfo:
    """Tests for info command in chains."""

    def test_info_passthrough_to_convert(self, sample_landscape_image, temp_dir):
        """info + convert: info passes through input file to convert."""
        output_convert = temp_dir / 'converted'

        result = run_ipro(
            'info', str(sample_landscape_image),
            '+',
            'convert', '--format', 'webp',
            '--output', str(output_convert),
        )

        assert result.returncode == 0
        # Info output should appear
        assert 'landscape.jpg' in result.stdout
        # Convert should have created the file
        converted_files = list(output_convert.glob('*.webp'))
        assert len(converted_files) == 1


class TestChainErrorHandling:
    """Tests for error handling in chains."""

    def test_first_command_file_not_found(self, temp_dir):
        """Error in first command aborts entire chain."""
        result = run_ipro(
            'resize', '/nonexistent/photo.jpg',
            '--width', '300',
            '+',
            'convert', '--format', 'webp',
        )

        assert result.returncode == 3  # file not found
        assert 'Error' in result.stderr

    def test_second_command_error(self, sample_landscape_image, temp_dir):
        """Error in second command exits with appropriate code."""
        output_resize = temp_dir / 'resized'

        result = run_ipro(
            'resize', str(sample_landscape_image),
            '--width', '300',
            '--output', str(output_resize),
            '+',
            'convert', '--format', 'bmp',  # unsupported format
        )

        # Convert should fail with exit code 2 (invalid arguments)
        assert result.returncode == 2

    def test_empty_chain_from_skipped_resize(self, sample_landscape_image, temp_dir):
        """If resize skips all sizes (upscaling), chain continues with empty output."""
        output_resize = temp_dir / 'resized'
        output_convert = temp_dir / 'converted'

        result = run_ipro(
            'resize', str(sample_landscape_image),
            '--width', '9999',  # larger than 1920px original
            '--output', str(output_resize),
            '+',
            'convert', '--format', 'webp',
            '--output', str(output_convert),
        )

        # Should succeed but produce no convert output (no inputs to convert)
        assert result.returncode == 0
        converted_files = list(output_convert.glob('*')) if output_convert.exists() else []
        assert len(converted_files) == 0


class TestSingleCommandUnchanged:
    """Verify that single commands (no chain) still work as before."""

    def test_single_info(self, sample_landscape_image):
        """Single info command works unchanged."""
        result = run_ipro('info', str(sample_landscape_image))
        assert result.returncode == 0
        assert 'landscape.jpg' in result.stdout

    def test_single_resize(self, sample_landscape_image, temp_dir):
        """Single resize command works unchanged."""
        output_dir = temp_dir / 'resized'
        result = run_ipro(
            'resize', str(sample_landscape_image),
            '--width', '300',
            '--output', str(output_dir),
        )
        assert result.returncode == 0
        assert len(list(output_dir.glob('*.jpg'))) == 1

    def test_single_convert(self, sample_landscape_image, temp_dir):
        """Single convert command works unchanged."""
        output_dir = temp_dir / 'converted'
        result = run_ipro(
            'convert', str(sample_landscape_image),
            '--format', 'webp',
            '--output', str(output_dir),
        )
        assert result.returncode == 0
        assert len(list(output_dir.glob('*.webp'))) == 1

    def test_no_command_shows_help(self):
        """No command shows help text."""
        result = run_ipro()
        assert result.returncode == 0


class TestChainOutput:
    """Tests for chain output messages."""

    def test_chain_shows_all_command_output(self, sample_landscape_image, temp_dir):
        """Chain shows output from all commands in sequence."""
        output_resize = temp_dir / 'resized'
        output_convert = temp_dir / 'converted'

        result = run_ipro(
            'resize', str(sample_landscape_image),
            '--width', '300',
            '--output', str(output_resize),
            '+',
            'convert', '--format', 'webp',
            '--output', str(output_convert),
        )

        assert result.returncode == 0
        # Should see resize output
        assert 'Created' in result.stdout
        # Should see convert output
        assert 'webp' in result.stdout.lower() or 'Created' in result.stdout
