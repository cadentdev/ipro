"""Tests for MPO format support (issue #17) and extract subcommand (issue #18)."""

import subprocess
import sys
from pathlib import Path
from PIL import Image

import pytest


IMGPRO = str(Path(__file__).parent.parent / 'imgpro.py')


def run_imgpro(*args):
    """Run imgpro as a subprocess and return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, IMGPRO] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


# ── Issue #17: MPO format recognition ──


class TestMPOFormatMap:
    """Test that MPO is mapped correctly in the format system."""

    def test_get_format_extension_maps_mpo_to_jpg(self):
        """get_format_extension('MPO') returns '.jpg'."""
        from imgpro import get_format_extension
        assert get_format_extension('MPO') == '.jpg'

    def test_get_image_format_returns_mpo(self, sample_mpo_image):
        """get_image_format returns 'MPO' for MPO files, not 'JPEG'."""
        from imgpro import get_image_format
        fmt = get_image_format(sample_mpo_image)
        assert fmt == 'MPO'


class TestMPORename:
    """Test rename --ext with MPO files."""

    def test_rename_ext_mpo_gets_jpg_extension(self, sample_mpo_image, temp_dir):
        """rename --ext on MPO file produces .jpg, not .mpo."""
        exit_code, stdout, stderr = run_imgpro(
            'rename', str(sample_mpo_image), '--ext',
            '--output', str(temp_dir / 'out')
        )
        assert exit_code == 0
        assert '.jpg' in stdout
        assert '.mpo' not in stdout


class TestMPOResize:
    """Test resize with MPO files."""

    def test_resize_accepts_mpo(self, sample_mpo_image, temp_dir):
        """resize does not reject MPO files."""
        exit_code, stdout, stderr = run_imgpro(
            'resize', str(sample_mpo_image), '--width', '400',
            '--output', str(temp_dir / 'out')
        )
        assert exit_code == 0
        assert 'Unsupported format' not in stderr
        assert 'Created' in stdout or 'created' in stdout.lower()

    def test_resize_mpo_produces_output(self, sample_mpo_image, temp_dir):
        """resize on MPO file creates an output file."""
        out_dir = temp_dir / 'resized'
        exit_code, stdout, stderr = run_imgpro(
            'resize', str(sample_mpo_image), '--width', '400',
            '--output', str(out_dir)
        )
        assert exit_code == 0
        output_files = list(out_dir.iterdir())
        assert len(output_files) == 1


class TestMPOConvert:
    """Test convert with MPO files."""

    def test_convert_mpo_warns_about_frames(self, sample_mpo_image, temp_dir):
        """convert on MPO file warns about dropped frames."""
        exit_code, stdout, stderr = run_imgpro(
            'convert', str(sample_mpo_image), '--format', 'png',
            '--output', str(temp_dir / 'out')
        )
        assert exit_code == 0
        assert 'frames' in stderr.lower()
        assert 'extract' in stderr.lower()

    def test_convert_mpo_succeeds(self, sample_mpo_image, temp_dir):
        """convert on MPO file produces output."""
        out_dir = temp_dir / 'converted'
        exit_code, stdout, stderr = run_imgpro(
            'convert', str(sample_mpo_image), '--format', 'png',
            '--output', str(out_dir)
        )
        assert exit_code == 0
        assert 'Created' in stdout


class TestMPOInfo:
    """Test info with MPO files."""

    def test_info_shows_format(self, sample_mpo_image):
        """info output includes Format: MPO."""
        exit_code, stdout, stderr = run_imgpro('info', str(sample_mpo_image))
        assert exit_code == 0
        assert 'Format: MPO' in stdout

    def test_info_shows_frame_count(self, sample_mpo_image):
        """info output shows Frames: 2 for multi-frame MPO."""
        exit_code, stdout, stderr = run_imgpro('info', str(sample_mpo_image))
        assert exit_code == 0
        assert 'Frames: 2' in stdout

    def test_info_json_includes_format_and_frames(self, sample_mpo_image):
        """info --json output includes format and frames fields."""
        import json
        exit_code, stdout, stderr = run_imgpro('info', str(sample_mpo_image), '--json')
        assert exit_code == 0
        data = json.loads(stdout)
        assert data['format'] == 'MPO'
        assert data['frames'] == 2

    def test_info_single_frame_hides_frame_count(self, sample_square_image):
        """info on single-frame JPEG does not show Frames line."""
        exit_code, stdout, stderr = run_imgpro('info', str(sample_square_image))
        assert exit_code == 0
        assert 'Frames:' not in stdout
        assert 'Format: JPEG' in stdout


# ── Issue #18: extract subcommand ──


class TestExtractBasic:
    """Test extract subcommand core functionality."""

    def test_extract_mpo_produces_two_files(self, sample_mpo_image, temp_dir):
        """extract on 2-frame MPO produces 2 output files."""
        out_dir = temp_dir / 'frames'
        exit_code, stdout, stderr = run_imgpro(
            'extract', str(sample_mpo_image),
            '--output', str(out_dir)
        )
        assert exit_code == 0
        output_files = sorted(out_dir.iterdir())
        assert len(output_files) == 2

    def test_extract_output_naming(self, sample_mpo_image, temp_dir):
        """extract uses {basename}_{NNN}.{ext} naming pattern."""
        out_dir = temp_dir / 'frames'
        exit_code, stdout, stderr = run_imgpro(
            'extract', str(sample_mpo_image),
            '--output', str(out_dir)
        )
        assert exit_code == 0
        output_files = sorted(f.name for f in out_dir.iterdir())
        assert output_files == ['stereo_001.jpg', 'stereo_002.jpg']

    def test_extract_frames_are_valid_images(self, sample_mpo_image, temp_dir):
        """extracted frames are valid, openable images."""
        out_dir = temp_dir / 'frames'
        run_imgpro('extract', str(sample_mpo_image), '--output', str(out_dir))
        for f in out_dir.iterdir():
            img = Image.open(f)
            assert img.size[0] > 0
            assert img.size[1] > 0

    def test_extract_prints_summary(self, sample_mpo_image, temp_dir):
        """extract prints extraction summary."""
        out_dir = temp_dir / 'frames'
        exit_code, stdout, stderr = run_imgpro(
            'extract', str(sample_mpo_image),
            '--output', str(out_dir)
        )
        assert exit_code == 0
        assert 'Extracted 2 frame(s)' in stdout


class TestExtractSingleFrame:
    """Test extract on single-frame images."""

    def test_extract_single_frame_produces_one_file(self, sample_square_image, temp_dir):
        """extract on single-frame JPEG produces 1 output file."""
        out_dir = temp_dir / 'frames'
        exit_code, stdout, stderr = run_imgpro(
            'extract', str(sample_square_image),
            '--output', str(out_dir)
        )
        assert exit_code == 0
        output_files = list(out_dir.iterdir())
        assert len(output_files) == 1

    def test_extract_single_frame_note(self, sample_square_image, temp_dir):
        """extract on single-frame image prints informational note."""
        out_dir = temp_dir / 'frames'
        exit_code, stdout, stderr = run_imgpro(
            'extract', str(sample_square_image),
            '--output', str(out_dir)
        )
        assert exit_code == 0
        assert 'only 1 frame' in stdout.lower()


class TestExtractChaining:
    """Test extract chaining with other commands via +."""

    def test_extract_chain_to_resize(self, sample_mpo_image, temp_dir):
        """extract + resize chains correctly."""
        exit_code, stdout, stderr = run_imgpro(
            'extract', str(sample_mpo_image),
            '--output', str(temp_dir / 'frames'),
            '+', 'resize', '--width', '400',
            '--output', str(temp_dir / 'resized')
        )
        assert exit_code == 0
        resized_dir = temp_dir / 'resized'
        resized_files = list(resized_dir.iterdir())
        assert len(resized_files) == 2


class TestExtractEdgeCases:
    """Test extract edge cases."""

    def test_extract_nonexistent_file(self, temp_dir):
        """extract on nonexistent file exits with error."""
        exit_code, stdout, stderr = run_imgpro(
            'extract', str(temp_dir / 'does_not_exist.jpg')
        )
        assert exit_code != 0

    def test_extract_creates_output_dir(self, sample_mpo_image, temp_dir):
        """extract creates output directory if it doesn't exist."""
        out_dir = temp_dir / 'nested' / 'deep' / 'frames'
        exit_code, stdout, stderr = run_imgpro(
            'extract', str(sample_mpo_image),
            '--output', str(out_dir)
        )
        assert exit_code == 0
        assert out_dir.exists()
