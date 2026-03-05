"""CLI integration tests for ipro rename command."""

import pytest
import subprocess
import sys
from pathlib import Path
from PIL import Image


def run_ipro_rename(filepath, *args):
    """
    Run ipro rename command and return result.

    Args:
        filepath: Path to image file
        *args: Additional CLI arguments

    Returns:
        tuple: (exit_code, stdout, stderr)
    """
    cmd = [sys.executable, 'ipro.py', 'rename', str(filepath)] + list(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    return result.returncode, result.stdout, result.stderr


class TestRenameCommandBasics:
    """Test basic rename command functionality."""

    def test_rename_command_exists(self):
        """Test that rename subcommand is recognized."""
        cmd = [sys.executable, 'ipro.py', 'rename', '--help']
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        # Should not fail and should mention 'rename'
        assert result.returncode == 0
        assert 'rename' in result.stdout.lower()

    def test_rename_requires_file_argument(self):
        """Test that rename command requires a file argument."""
        cmd = [sys.executable, 'ipro.py', 'rename']
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        # Should fail with non-zero exit code
        assert result.returncode != 0

    def test_rename_requires_action_flag(self, sample_square_image):
        """Test that rename requires at least --ext or --prefix-exif-date."""
        exit_code, stdout, stderr = run_ipro_rename(sample_square_image)
        # Should fail because no action flag provided
        assert exit_code != 0
        assert 'ext' in stderr.lower() or 'prefix' in stderr.lower() or 'required' in stderr.lower()

    def test_rename_file_not_found(self, temp_dir):
        """Test error handling for non-existent file."""
        fake_file = temp_dir / 'does_not_exist.jpg'
        exit_code, stdout, stderr = run_ipro_rename(fake_file, '--ext')

        # Should exit with code 3 (file not found)
        assert exit_code == 3
        assert 'not found' in stderr.lower()

    def test_rename_unsupported_file(self, sample_non_image_file):
        """Test error handling for non-image file."""
        exit_code, stdout, stderr = run_ipro_rename(sample_non_image_file, '--ext')

        # Should exit with code 4 (cannot read)
        assert exit_code == 4


class TestRenameExtFlag:
    """Test --ext flag for extension correction."""

    def test_ext_corrects_mismatched_extension(self, temp_dir):
        """Test that --ext corrects mismatched extension."""
        # Create a JPEG file with .HEIC extension
        img = Image.new('RGB', (100, 100), (255, 0, 0))
        fake_heic = temp_dir / "photo.HEIC"
        img.save(fake_heic, 'JPEG')

        exit_code, stdout, stderr = run_ipro_rename(fake_heic, '--ext')

        assert exit_code == 0
        # Check that new file was created with .jpg extension in renamed/ subdir
        expected_output = temp_dir / "renamed" / "photo.jpg"
        assert expected_output.exists()
        # Original should still exist (non-destructive)
        assert fake_heic.exists()

    def test_ext_normalizes_to_lowercase(self, temp_dir):
        """Test that --ext normalizes extension to lowercase."""
        # Create a JPEG file with uppercase .JPG extension
        img = Image.new('RGB', (100, 100), (255, 0, 0))
        uppercase_jpg = temp_dir / "photo.JPG"
        img.save(uppercase_jpg, 'JPEG')

        exit_code, stdout, stderr = run_ipro_rename(uppercase_jpg, '--ext')

        assert exit_code == 0
        # On case-insensitive filesystems (macOS, Windows), photo.jpg and photo.JPG
        # are the same file. The command should succeed either way.
        expected_output = temp_dir / "renamed" / "photo.jpg"
        # Check that a file with the correct name exists (case-insensitive check)
        matching_files = list((temp_dir / "renamed").glob("photo.[jJ][pP][gG]"))
        assert len(matching_files) >= 1

    def test_ext_creates_copy_not_moves(self, temp_dir):
        """Test that --ext creates a copy, not moves/renames."""
        img = Image.new('RGB', (100, 100), (255, 0, 0))
        original = temp_dir / "photo.HEIC"
        img.save(original, 'JPEG')

        run_ipro_rename(original, '--ext')

        # Original should still exist
        assert original.exists()
        # New file should also exist in renamed/ subdir
        assert (temp_dir / "renamed" / "photo.jpg").exists()

    def test_ext_png_keeps_png_extension(self, sample_png_image):
        """Test that PNG file gets .png extension."""
        exit_code, stdout, stderr = run_ipro_rename(sample_png_image, '--ext')

        assert exit_code == 0
        # File already has correct extension, should report no change needed
        # or the file should exist
        expected_output = sample_png_image.parent / "renamed" / "test.png"
        assert expected_output.exists()
        # Output should indicate no change or success
        combined = stdout + stderr
        assert 'no change' in combined.lower() or 'created' in combined.lower()

    def test_ext_output_message(self, temp_dir):
        """Test that --ext outputs success message."""
        img = Image.new('RGB', (100, 100), (255, 0, 0))
        original = temp_dir / "photo.HEIC"
        img.save(original, 'JPEG')

        exit_code, stdout, stderr = run_ipro_rename(original, '--ext')

        assert exit_code == 0
        # Should mention both original and new filename
        assert 'photo.jpg' in stdout or 'photo.jpg' in stderr


class TestRenamePrefixExifDate:
    """Test --prefix-exif-date flag."""

    def test_prefix_exif_date_adds_prefix(self, sample_image_with_exif):
        """Test that --prefix-exif-date adds date prefix."""
        exit_code, stdout, stderr = run_ipro_rename(
            sample_image_with_exif, '--prefix-exif-date'
        )

        assert exit_code == 0
        # Check that new file was created with date prefix in renamed/ subdir
        parent_dir = sample_image_with_exif.parent
        # The fixture uses EXIF_DATA_FULL which has date "2024:11:12 14:30:00"
        expected_output = parent_dir / "renamed" / "2024-11-12T143000_with_exif.jpg"
        assert expected_output.exists()

    def test_prefix_exif_date_no_colons_in_output(self, sample_image_with_exif):
        """Test that date prefix contains no colons (macOS-safe)."""
        exit_code, stdout, stderr = run_ipro_rename(
            sample_image_with_exif, '--prefix-exif-date'
        )

        assert exit_code == 0
        parent_dir = sample_image_with_exif.parent / "renamed"
        # Find the new file
        new_files = [f for f in parent_dir.iterdir()
                     if f.name.startswith('2024-')]
        assert len(new_files) == 1
        # Filename should not contain colons
        assert ':' not in new_files[0].name

    def test_prefix_exif_date_skips_no_exif(self, sample_image_no_exif):
        """Test that --prefix-exif-date skips files without EXIF date."""
        exit_code, stdout, stderr = run_ipro_rename(
            sample_image_no_exif, '--prefix-exif-date'
        )

        # Should exit successfully but with warning
        assert exit_code == 0
        # Should warn about missing date
        combined = stdout + stderr
        assert 'skip' in combined.lower() or 'no' in combined.lower() or 'warning' in combined.lower()
        # No new file should be created
        parent_dir = sample_image_no_exif.parent
        files_starting_with_date = [f for f in parent_dir.iterdir()
                                     if f.name[0].isdigit()]
        assert len(files_starting_with_date) == 0

    def test_prefix_exif_date_preserves_original(self, sample_image_with_exif):
        """Test that original file is preserved."""
        original_exists_before = sample_image_with_exif.exists()
        run_ipro_rename(sample_image_with_exif, '--prefix-exif-date')

        assert original_exists_before
        assert sample_image_with_exif.exists()


class TestRenameCombinedFlags:
    """Test combining --ext and --prefix-exif-date flags."""

    def test_combined_flags(self, temp_dir):
        """Test using both --ext and --prefix-exif-date together."""
        from .fixtures import create_test_image_file, EXIF_DATA_FULL

        # Create a JPEG with .HEIC extension and EXIF data
        img_path = create_test_image_file(
            800, 600,
            directory=temp_dir,
            filename='photo.HEIC',
            exif_data=EXIF_DATA_FULL
        )
        # Re-save as JPEG (the fixture creates JPEG internally)

        exit_code, stdout, stderr = run_ipro_rename(
            img_path, '--ext', '--prefix-exif-date'
        )

        assert exit_code == 0
        # Should have date prefix AND corrected extension
        # EXIF_DATA_FULL has date "2024:11:12 14:30:00"
        expected = temp_dir / "renamed" / "2024-11-12T143000_photo.jpg"
        assert expected.exists()

    def test_combined_flags_order_independent(self, temp_dir):
        """Test that flag order doesn't matter."""
        from .fixtures import create_test_image_file, EXIF_DATA_FULL

        img_path = create_test_image_file(
            800, 600,
            directory=temp_dir,
            filename='test.HEIC',
            exif_data=EXIF_DATA_FULL
        )

        # Try with reversed order
        exit_code, stdout, stderr = run_ipro_rename(
            img_path, '--prefix-exif-date', '--ext'
        )

        assert exit_code == 0
        expected = temp_dir / "renamed" / "2024-11-12T143000_test.jpg"
        assert expected.exists()


class TestRenameOutputDirectory:
    """Test --output option for custom output directory."""

    def test_output_directory_option(self, temp_dir):
        """Test --output specifies custom output directory."""
        # Create a JPEG with mismatched extension
        img = Image.new('RGB', (100, 100), (255, 0, 0))
        original = temp_dir / "photo.HEIC"
        img.save(original, 'JPEG')

        output_dir = temp_dir / "renamed"
        output_dir.mkdir()

        exit_code, stdout, stderr = run_ipro_rename(
            original, '--ext', '--output', str(output_dir)
        )

        assert exit_code == 0
        # File should be in output directory with corrected extension
        expected = output_dir / "photo.jpg"
        assert expected.exists()
        # Original file should still exist
        assert original.exists()
        # No copy should be in original location with the new name
        assert not (temp_dir / "photo.jpg").exists()

    def test_output_directory_created_if_not_exists(self, temp_dir, sample_square_image):
        """Test that output directory is created if it doesn't exist."""
        output_dir = temp_dir / "new_output_dir"
        assert not output_dir.exists()

        exit_code, stdout, stderr = run_ipro_rename(
            sample_square_image, '--ext', '--output', str(output_dir)
        )

        assert exit_code == 0
        assert output_dir.exists()
        assert (output_dir / "square.jpg").exists()


class TestRenameExitCodes:
    """Test exit codes for various scenarios."""

    def test_success_exit_code(self, temp_dir):
        """Test successful rename returns exit code 0."""
        img = Image.new('RGB', (100, 100), (255, 0, 0))
        original = temp_dir / "photo.HEIC"
        img.save(original, 'JPEG')

        exit_code, _, _ = run_ipro_rename(original, '--ext')
        assert exit_code == 0

    def test_file_not_found_exit_code(self, temp_dir):
        """Test file not found returns exit code 3."""
        exit_code, _, _ = run_ipro_rename(
            temp_dir / "nonexistent.jpg", '--ext'
        )
        assert exit_code == 3

    def test_cannot_read_exit_code(self, sample_non_image_file):
        """Test unreadable file returns exit code 4."""
        exit_code, _, _ = run_ipro_rename(
            sample_non_image_file, '--ext'
        )
        assert exit_code == 4

    def test_skip_no_exif_date_still_success(self, sample_image_no_exif):
        """Test that skipping file due to no EXIF date still returns 0."""
        exit_code, _, _ = run_ipro_rename(
            sample_image_no_exif, '--prefix-exif-date'
        )
        # Should be 0 (skip with warning, not error)
        assert exit_code == 0


class TestRenameEdgeCases:
    """Test edge cases and special scenarios."""

    def test_filename_with_spaces(self, temp_dir):
        """Test handling filenames with spaces."""
        img = Image.new('RGB', (100, 100), (255, 0, 0))
        original = temp_dir / "my photo.HEIC"
        img.save(original, 'JPEG')

        exit_code, stdout, stderr = run_ipro_rename(original, '--ext')

        assert exit_code == 0
        expected = temp_dir / "renamed" / "my photo.jpg"
        assert expected.exists()

    def test_filename_with_multiple_dots(self, temp_dir):
        """Test handling filenames with multiple dots."""
        img = Image.new('RGB', (100, 100), (255, 0, 0))
        original = temp_dir / "photo.backup.HEIC"
        img.save(original, 'JPEG')

        exit_code, stdout, stderr = run_ipro_rename(original, '--ext')

        assert exit_code == 0
        expected = temp_dir / "renamed" / "photo.backup.jpg"
        assert expected.exists()

    def test_output_file_already_exists(self, temp_dir):
        """Test behavior when output file already exists."""
        img = Image.new('RGB', (100, 100), (255, 0, 0))
        original = temp_dir / "photo.HEIC"
        img.save(original, 'JPEG')

        # Create existing output file in renamed/ subdir
        renamed_dir = temp_dir / "renamed"
        renamed_dir.mkdir()
        existing = renamed_dir / "photo.jpg"
        existing.write_text("existing content")

        exit_code, stdout, stderr = run_ipro_rename(original, '--ext')

        # Should overwrite with warning (or could fail - depends on design)
        # For now, let's say it should succeed and overwrite
        assert exit_code == 0
        assert existing.exists()
        # Verify it's actually an image now (not text)
        with Image.open(existing) as img:
            assert img.size == (100, 100)

    def test_unicode_filename(self, temp_dir):
        """Test handling unicode in filenames."""
        img = Image.new('RGB', (100, 100), (255, 0, 0))
        original = temp_dir / "фото.HEIC"  # Russian word for "photo"
        img.save(original, 'JPEG')

        exit_code, stdout, stderr = run_ipro_rename(original, '--ext')

        assert exit_code == 0
        expected = temp_dir / "renamed" / "фото.jpg"
        assert expected.exists()
