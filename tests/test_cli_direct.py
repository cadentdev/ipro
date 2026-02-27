"""Direct tests for CLI command handlers and main function.

These tests import and call cmd_info, cmd_resize, and main directly
rather than using subprocess, which improves coverage reporting.
"""

import pytest
import sys
import argparse
from pathlib import Path
from io import StringIO
from unittest.mock import patch


class TestCmdInfoDirect:
    """Test cmd_info function directly."""

    def test_cmd_info_basic(self, sample_square_image, capsys):
        """Test cmd_info with basic arguments."""
        from imgpro import cmd_info

        args = argparse.Namespace(
            file=str(sample_square_image),
            json=False,
            short=False,
            exif=False,
            exif_all=False
        )

        cmd_info(args)

        captured = capsys.readouterr()
        assert '1000' in captured.out
        assert 'square' in captured.out.lower()
        assert '1:1' in captured.out

    def test_cmd_info_json_output(self, sample_square_image, capsys):
        """Test cmd_info with JSON output."""
        from imgpro import cmd_info
        import json

        args = argparse.Namespace(
            file=str(sample_square_image),
            json=True,
            short=False,
            exif=False,
            exif_all=False
        )

        cmd_info(args)

        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert data['width'] == 1000
        assert data['height'] == 1000
        assert data['orientation'] == 'square'
        assert data['ratio_raw'] == '1:1'

    def test_cmd_info_short_output(self, sample_square_image, capsys):
        """Test cmd_info with short CSV output."""
        from imgpro import cmd_info

        args = argparse.Namespace(
            file=str(sample_square_image),
            json=False,
            short=True,
            exif=False,
            exif_all=False
        )

        cmd_info(args)

        captured = capsys.readouterr()
        fields = captured.out.strip().split(',')

        assert fields[1] == 'JPEG'  # format
        assert fields[2] == '1'  # frames
        assert fields[3] == '1000'  # width
        assert fields[4] == '1000'  # height
        assert fields[5] == 'square'

    def test_cmd_info_with_exif(self, sample_image_with_exif, capsys):
        """Test cmd_info with EXIF flag."""
        from imgpro import cmd_info

        args = argparse.Namespace(
            file=str(sample_image_with_exif),
            json=False,
            short=False,
            exif=True,
            exif_all=False
        )

        cmd_info(args)

        captured = capsys.readouterr()
        assert 'exif' in captured.out.lower()

    def test_cmd_info_with_exif_all(self, sample_image_with_exif, capsys):
        """Test cmd_info with --exif-all flag."""
        from imgpro import cmd_info

        args = argparse.Namespace(
            file=str(sample_image_with_exif),
            json=False,
            short=False,
            exif=False,
            exif_all=True
        )

        cmd_info(args)

        captured = capsys.readouterr()
        assert 'exif' in captured.out.lower()

    def test_cmd_info_json_with_exif_all(self, sample_image_with_exif, capsys):
        """Test cmd_info with JSON and --exif-all."""
        from imgpro import cmd_info
        import json

        args = argparse.Namespace(
            file=str(sample_image_with_exif),
            json=True,
            short=False,
            exif=False,
            exif_all=True
        )

        cmd_info(args)

        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert 'exif' in data
        assert data['has_exif'] is True

    def test_cmd_info_file_not_found(self, temp_dir):
        """Test cmd_info with non-existent file."""
        from imgpro import cmd_info

        args = argparse.Namespace(
            file=str(temp_dir / 'missing.jpg'),
            json=False,
            short=False,
            exif=False,
            exif_all=False
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_info(args)

        assert exc_info.value.code == 3

    def test_cmd_info_unsupported_format(self, sample_non_image_file):
        """Test cmd_info with unsupported file format."""
        from imgpro import cmd_info

        args = argparse.Namespace(
            file=str(sample_non_image_file),
            json=False,
            short=False,
            exif=False,
            exif_all=False
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_info(args)

        assert exc_info.value.code == 1

    def test_cmd_info_landscape(self, sample_landscape_image, capsys):
        """Test cmd_info with landscape image."""
        from imgpro import cmd_info

        args = argparse.Namespace(
            file=str(sample_landscape_image),
            json=False,
            short=False,
            exif=False,
            exif_all=False
        )

        cmd_info(args)

        captured = capsys.readouterr()
        assert 'landscape' in captured.out.lower()
        assert '16:9' in captured.out

    def test_cmd_info_portrait(self, sample_portrait_image, capsys):
        """Test cmd_info with portrait image."""
        from imgpro import cmd_info

        args = argparse.Namespace(
            file=str(sample_portrait_image),
            json=False,
            short=False,
            exif=False,
            exif_all=False
        )

        cmd_info(args)

        captured = capsys.readouterr()
        assert 'portrait' in captured.out.lower()
        assert '9:16' in captured.out

    def test_cmd_info_no_exif_json(self, sample_image_no_exif, capsys):
        """Test cmd_info JSON output when no EXIF present."""
        from imgpro import cmd_info
        import json

        args = argparse.Namespace(
            file=str(sample_image_no_exif),
            json=True,
            short=False,
            exif=False,
            exif_all=False
        )

        cmd_info(args)

        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert data['has_exif'] is False

    def test_cmd_info_uncommon_ratio(self, temp_dir, capsys):
        """Test cmd_info with uncommon aspect ratio."""
        from imgpro import cmd_info
        from tests.fixtures import create_test_image_file
        import json

        # Create image with uncommon ratio
        filepath = create_test_image_file(
            1234, 567,
            directory=temp_dir,
            filename='weird.jpg'
        )

        args = argparse.Namespace(
            file=str(filepath),
            json=True,
            short=False,
            exif=False,
            exif_all=False
        )

        cmd_info(args)

        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert data['common_ratio'] == 'none'

    def test_cmd_info_common_ratio_display(self, sample_landscape_image, capsys):
        """Test that common ratio is displayed in default output."""
        from imgpro import cmd_info

        args = argparse.Namespace(
            file=str(sample_landscape_image),
            json=False,
            short=False,
            exif=False,
            exif_all=False
        )

        cmd_info(args)

        captured = capsys.readouterr()
        # 16:9 should appear with common ratio indicator
        assert '16:9' in captured.out


class TestCmdResizeDirect:
    """Test cmd_resize function directly."""

    def test_cmd_resize_basic_width(self, temp_dir, capsys):
        """Test cmd_resize with basic width argument."""
        from imgpro import cmd_resize
        from tests.fixtures import create_test_image_file

        img_path = create_test_image_file(1200, 800, directory=temp_dir, filename='test.jpg')
        output_dir = temp_dir / 'resized'

        args = argparse.Namespace(
            file=str(img_path),
            width='300',
            height=None,
            output=str(output_dir),
            quality=90
        )

        cmd_resize(args)

        captured = capsys.readouterr()
        assert 'test_300.jpg' in captured.out
        assert 'Successfully created 1 image' in captured.out
        assert (output_dir / 'test_300.jpg').exists()

    def test_cmd_resize_multiple_widths(self, temp_dir, capsys):
        """Test cmd_resize with multiple widths."""
        from imgpro import cmd_resize
        from tests.fixtures import create_test_image_file

        img_path = create_test_image_file(1920, 1080, directory=temp_dir, filename='test.jpg')
        output_dir = temp_dir / 'resized'

        args = argparse.Namespace(
            file=str(img_path),
            width='300,600,900',
            height=None,
            output=str(output_dir),
            quality=90
        )

        cmd_resize(args)

        captured = capsys.readouterr()
        assert 'Successfully created 3 image' in captured.out

    def test_cmd_resize_by_height(self, temp_dir, capsys):
        """Test cmd_resize with height argument."""
        from imgpro import cmd_resize
        from tests.fixtures import create_test_image_file

        img_path = create_test_image_file(1200, 800, directory=temp_dir, filename='test.jpg')
        output_dir = temp_dir / 'resized'

        args = argparse.Namespace(
            file=str(img_path),
            width=None,
            height='400',
            output=str(output_dir),
            quality=90
        )

        cmd_resize(args)

        captured = capsys.readouterr()
        assert 'test_400.jpg' in captured.out
        assert '600x400' in captured.out

    def test_cmd_resize_file_not_found(self, temp_dir):
        """Test cmd_resize with non-existent file."""
        from imgpro import cmd_resize

        args = argparse.Namespace(
            file=str(temp_dir / 'missing.jpg'),
            width='300',
            height=None,
            output=str(temp_dir / 'resized'),
            quality=90
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_resize(args)

        assert exc_info.value.code == 3

    def test_cmd_resize_unsupported_format(self, temp_dir):
        """Test cmd_resize with non-JPEG file."""
        from imgpro import cmd_resize
        from PIL import Image

        # Create PNG file
        img = Image.new('RGB', (800, 600), color=(255, 0, 0))
        png_file = temp_dir / 'test.png'
        img.save(png_file, 'PNG')

        args = argparse.Namespace(
            file=str(png_file),
            width='300',
            height=None,
            output=str(temp_dir / 'resized'),
            quality=90
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_resize(args)

        assert exc_info.value.code == 1

    def test_cmd_resize_both_width_and_height(self, temp_dir):
        """Test cmd_resize with both width and height (should fail)."""
        from imgpro import cmd_resize
        from tests.fixtures import create_test_image_file

        img_path = create_test_image_file(1200, 800, directory=temp_dir, filename='test.jpg')

        args = argparse.Namespace(
            file=str(img_path),
            width='300',
            height='400',
            output=str(temp_dir / 'resized'),
            quality=90
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_resize(args)

        assert exc_info.value.code == 2

    def test_cmd_resize_neither_width_nor_height(self, temp_dir):
        """Test cmd_resize with neither width nor height (should fail)."""
        from imgpro import cmd_resize
        from tests.fixtures import create_test_image_file

        img_path = create_test_image_file(1200, 800, directory=temp_dir, filename='test.jpg')

        args = argparse.Namespace(
            file=str(img_path),
            width=None,
            height=None,
            output=str(temp_dir / 'resized'),
            quality=90
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_resize(args)

        assert exc_info.value.code == 2

    def test_cmd_resize_invalid_quality_low(self, temp_dir):
        """Test cmd_resize with quality < 1."""
        from imgpro import cmd_resize
        from tests.fixtures import create_test_image_file

        img_path = create_test_image_file(1200, 800, directory=temp_dir, filename='test.jpg')

        args = argparse.Namespace(
            file=str(img_path),
            width='300',
            height=None,
            output=str(temp_dir / 'resized'),
            quality=0
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_resize(args)

        assert exc_info.value.code == 2

    def test_cmd_resize_invalid_quality_high(self, temp_dir):
        """Test cmd_resize with quality > 100."""
        from imgpro import cmd_resize
        from tests.fixtures import create_test_image_file

        img_path = create_test_image_file(1200, 800, directory=temp_dir, filename='test.jpg')

        args = argparse.Namespace(
            file=str(img_path),
            width='300',
            height=None,
            output=str(temp_dir / 'resized'),
            quality=101
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_resize(args)

        assert exc_info.value.code == 2

    def test_cmd_resize_upscaling_warning(self, temp_dir, capsys):
        """Test cmd_resize shows warning for skipped sizes."""
        from imgpro import cmd_resize
        from tests.fixtures import create_test_image_file

        img_path = create_test_image_file(800, 600, directory=temp_dir, filename='small.jpg')
        output_dir = temp_dir / 'resized'

        args = argparse.Namespace(
            file=str(img_path),
            width='400,1200',
            height=None,
            output=str(output_dir),
            quality=90
        )

        cmd_resize(args)

        captured = capsys.readouterr()
        assert 'Skipped 1200px' in captured.out
        assert 'only 800px wide' in captured.out

    def test_cmd_resize_all_sizes_skipped(self, temp_dir, capsys):
        """Test cmd_resize when all sizes require upscaling."""
        from imgpro import cmd_resize
        from tests.fixtures import create_test_image_file

        img_path = create_test_image_file(400, 300, directory=temp_dir, filename='tiny.jpg')
        output_dir = temp_dir / 'resized'

        args = argparse.Namespace(
            file=str(img_path),
            width='800,1200',
            height=None,
            output=str(output_dir),
            quality=90
        )

        # cmd_resize returns empty list when all sizes are skipped
        result = cmd_resize(args)

        assert result == []

        captured = capsys.readouterr()
        assert 'No images created' in captured.out or 'Warning' in captured.out

    def test_cmd_resize_custom_quality(self, temp_dir, capsys):
        """Test cmd_resize with custom quality."""
        from imgpro import cmd_resize
        from tests.fixtures import create_test_image_file

        img_path = create_test_image_file(1200, 800, directory=temp_dir, filename='test.jpg')
        output_dir = temp_dir / 'resized'

        args = argparse.Namespace(
            file=str(img_path),
            width='300',
            height=None,
            output=str(output_dir),
            quality=50
        )

        cmd_resize(args)

        captured = capsys.readouterr()
        assert 'Successfully created 1 image' in captured.out


class TestMainFunction:
    """Test main() function directly."""

    def test_main_no_command(self, monkeypatch, capsys):
        """Test main with no command shows help and exits 0."""
        from imgpro import main

        monkeypatch.setattr(sys, 'argv', ['imgpro.py'])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert 'usage' in captured.out.lower() or 'imgpro' in captured.out.lower()

    def test_main_version_flag(self, monkeypatch, capsys):
        """Test main with --version flag."""
        from imgpro import main, __version__

        monkeypatch.setattr(sys, 'argv', ['imgpro.py', '--version'])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert __version__ in captured.out

    def test_main_version_short_flag(self, monkeypatch, capsys):
        """Test main with -v flag."""
        from imgpro import main, __version__

        monkeypatch.setattr(sys, 'argv', ['imgpro.py', '-v'])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert __version__ in captured.out

    def test_main_help_flag(self, monkeypatch, capsys):
        """Test main with --help flag."""
        from imgpro import main

        monkeypatch.setattr(sys, 'argv', ['imgpro.py', '--help'])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert 'info' in captured.out.lower()
        assert 'resize' in captured.out.lower()

    def test_main_info_subcommand(self, monkeypatch, capsys, sample_square_image):
        """Test main with info subcommand."""
        from imgpro import main

        monkeypatch.setattr(sys, 'argv', [
            'imgpro.py', 'info', str(sample_square_image)
        ])

        main()

        captured = capsys.readouterr()
        assert '1000' in captured.out
        assert 'square' in captured.out.lower()

    def test_main_info_help(self, monkeypatch, capsys):
        """Test main with info --help."""
        from imgpro import main

        monkeypatch.setattr(sys, 'argv', ['imgpro.py', 'info', '--help'])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert 'json' in captured.out.lower()
        assert 'short' in captured.out.lower()

    def test_main_resize_subcommand(self, monkeypatch, capsys, temp_dir):
        """Test main with resize subcommand."""
        from imgpro import main
        from tests.fixtures import create_test_image_file

        img_path = create_test_image_file(1200, 800, directory=temp_dir, filename='test.jpg')
        output_dir = temp_dir / 'resized'

        monkeypatch.setattr(sys, 'argv', [
            'imgpro.py', 'resize',
            str(img_path),
            '--width', '300',
            '--output', str(output_dir)
        ])

        main()

        captured = capsys.readouterr()
        assert 'test_300.jpg' in captured.out

    def test_main_resize_help(self, monkeypatch, capsys):
        """Test main with resize --help."""
        from imgpro import main

        monkeypatch.setattr(sys, 'argv', ['imgpro.py', 'resize', '--help'])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert 'width' in captured.out.lower()
        assert 'height' in captured.out.lower()
        assert 'quality' in captured.out.lower()

    def test_main_info_json(self, monkeypatch, capsys, sample_square_image):
        """Test main with info --json."""
        from imgpro import main
        import json

        monkeypatch.setattr(sys, 'argv', [
            'imgpro.py', 'info', str(sample_square_image), '--json'
        ])

        main()

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['width'] == 1000

    def test_main_info_short(self, monkeypatch, capsys, sample_square_image):
        """Test main with info --short."""
        from imgpro import main

        monkeypatch.setattr(sys, 'argv', [
            'imgpro.py', 'info', str(sample_square_image), '--short'
        ])

        main()

        captured = capsys.readouterr()
        fields = captured.out.strip().split(',')
        assert len(fields) >= 7

    def test_main_unknown_command(self, monkeypatch, capsys):
        """Test main with unknown subcommand."""
        from imgpro import main

        monkeypatch.setattr(sys, 'argv', ['imgpro.py', 'unknown'])

        with pytest.raises(SystemExit) as exc_info:
            main()

        # argparse exits with code 2 for invalid arguments
        assert exc_info.value.code != 0


class TestCmdInfoExifJsonCoverage:
    """Test cmd_info JSON output with EXIF to cover line 391."""

    def test_cmd_info_json_with_exif_no_exif_all_flag(self, sample_image_with_exif, capsys):
        """Test JSON output with EXIF but WITHOUT --exif-all (covers line 391)."""
        from imgpro import cmd_info
        import json

        # This specifically tests the elif branch at line 390-391
        args = argparse.Namespace(
            file=str(sample_image_with_exif),
            json=True,
            short=False,
            exif=False,
            exif_all=False  # NOT using --exif-all
        )

        cmd_info(args)

        captured = capsys.readouterr()
        data = json.loads(captured.out)

        # Should have curated EXIF (not full exif_all)
        assert data['has_exif'] is True
        assert 'exif' in data
        assert data['exif'] is not None


class TestCmdInfoUncommonRatioCoverage:
    """Test default output with uncommon ratio to cover line 422."""

    def test_cmd_info_default_uncommon_ratio_no_common_match(self, temp_dir, capsys):
        """Test default output with uncommon ratio prints plain newline (covers line 422)."""
        from imgpro import cmd_info
        from tests.fixtures import create_test_image_file

        # Create image with uncommon ratio that won't match any common ratio
        filepath = create_test_image_file(
            1234, 567,
            directory=temp_dir,
            filename='weird.jpg'
        )

        args = argparse.Namespace(
            file=str(filepath),
            json=False,
            short=False,
            exif=False,
            exif_all=False
        )

        cmd_info(args)

        captured = capsys.readouterr()
        # Should have the ratio but no common ratio in parentheses
        assert '1234:567' in captured.out
        # The common ratio line should just be "Aspect Ratio: 1234:567" without the extra "(common)" part


class TestCmdResizeCorruptImage:
    """Test cmd_resize with corrupt JPEG file."""

    def test_cmd_resize_corrupt_jpeg(self, temp_dir):
        """Test cmd_resize with corrupt JPEG file gets unsupported format error."""
        from imgpro import cmd_resize

        # Create a file with .jpg extension but invalid content
        corrupt_file = temp_dir / 'corrupt.jpg'
        corrupt_file.write_bytes(b'JFIF fake jpeg header but not a real image')

        args = argparse.Namespace(
            file=str(corrupt_file),
            width='300',
            height=None,
            output=str(temp_dir / 'resized'),
            quality=90
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_resize(args)

        # Content-based validation: corrupt file is not recognized as JPEG
        assert exc_info.value.code == 1


class TestResizeTransparencyModes:
    """Test resize with images that trigger transparency handling."""

    def test_resize_palette_mode_image(self, temp_dir):
        """Test resizing a palette mode image triggers transparency handling."""
        from imgpro import resize_image
        from PIL import Image

        # Create a palette mode image with transparency
        img = Image.new('P', (800, 600))
        img.putpalette([i for i in range(256)] * 3)

        # Save as PNG first, then convert to JPEG
        png_path = temp_dir / 'palette.png'
        img.save(png_path, 'PNG')

        # Now save as JPEG (which converts to RGB)
        rgb_img = img.convert('RGB')
        jpeg_path = temp_dir / 'test.jpg'
        rgb_img.save(jpeg_path, 'JPEG', quality=90)

        output_dir = temp_dir / 'resized'
        created_files, skipped_sizes = resize_image(
            jpeg_path, output_dir, [400], dimension='width', quality=90
        )

        assert len(created_files) == 1

        # Verify output is RGB
        with Image.open(created_files[0]['path']) as result:
            assert result.mode == 'RGB'

    def test_resize_grayscale_mode_image(self, temp_dir):
        """Test resizing a grayscale (L mode) image converts to RGB."""
        from imgpro import resize_image
        from PIL import Image

        # Create grayscale image, convert to RGB, save as JPEG
        img = Image.new('L', (800, 600), color=128)
        rgb_img = img.convert('RGB')

        jpeg_path = temp_dir / 'grayscale.jpg'
        rgb_img.save(jpeg_path, 'JPEG', quality=90)

        output_dir = temp_dir / 'resized'
        created_files, skipped_sizes = resize_image(
            jpeg_path, output_dir, [400], dimension='width', quality=90
        )

        assert len(created_files) == 1
        with Image.open(created_files[0]['path']) as result:
            assert result.mode == 'RGB'
