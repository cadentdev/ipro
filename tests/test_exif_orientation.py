"""Tests for EXIF orientation handling (issue #24).

Images carrying an EXIF Orientation tag other than 1 (e.g. iPhone portrait
photos, Orientation=6) must have that orientation baked into the pixel data
before metadata is stripped or dimensions are measured. Otherwise outputs are
silently written sideways.
"""

import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))
import ipro  # noqa: E402

from .fixtures import (  # noqa: E402
    EXIF_ORIENTATION_TAG,
    create_oriented_image_file,
    is_blue,
    is_red,
)

IPRO = str(Path(__file__).parent.parent / 'ipro.py')


def run_ipro(*args):
    return subprocess.run(
        [sys.executable, IPRO] + [str(a) for a in args],
        capture_output=True,
        text=True,
    )


def _orientation_of(path):
    with Image.open(path) as img:
        return img.getexif().get(EXIF_ORIENTATION_TAG)


def _assert_portrait_red_on_top(path):
    """Displayed (stored, since tag must be gone/1) image is portrait, red top."""
    with Image.open(path) as img:
        img = img.convert('RGB')
        w, h = img.size
        assert h > w, f"expected portrait output, got {w}x{h}"
        assert is_red(img.getpixel((w // 2, h // 4)))
        assert is_blue(img.getpixel((w // 2, 3 * h // 4)))


@pytest.fixture
def iphone_portrait(temp_dir):
    """Stored 400x200 landscape pixels with Orientation=6 (displays 200x400)."""
    return create_oriented_image_file(temp_dir, 'IMG_5626.JPG',
                                      stored_size=(400, 200), orientation=6)


class TestApplyExifOrientationHelper:
    """Unit tests for apply_exif_orientation()."""

    def test_orientation_6_rotates_pixels(self, iphone_portrait):
        with Image.open(iphone_portrait) as img:
            out = ipro.apply_exif_orientation(img)
            assert out.size == (200, 400)
            assert is_red(out.convert('RGB').getpixel((100, 50)))

    def test_orientation_3_rotates_180(self, temp_dir):
        path = create_oriented_image_file(temp_dir, 'o3.jpg', orientation=3)
        with Image.open(path) as img:
            out = ipro.apply_exif_orientation(img).convert('RGB')
            assert out.size == (400, 200)
            # Stored left-red becomes right-red after 180°
            assert is_red(out.getpixel((300, 100)))
            assert is_blue(out.getpixel((100, 100)))

    def test_orientation_8_rotates_ccw(self, temp_dir):
        path = create_oriented_image_file(temp_dir, 'o8.jpg', orientation=8)
        with Image.open(path) as img:
            out = ipro.apply_exif_orientation(img).convert('RGB')
            assert out.size == (200, 400)
            # Stored left-red ends up on the bottom
            assert is_red(out.getpixel((100, 350)))

    def test_orientation_tag_cleared_after_transpose(self, iphone_portrait):
        with Image.open(iphone_portrait) as img:
            out = ipro.apply_exif_orientation(img)
            assert out.getexif().get(EXIF_ORIENTATION_TAG) in (None, 1)

    def test_no_orientation_returns_same_size(self, sample_landscape_image):
        with Image.open(sample_landscape_image) as img:
            out = ipro.apply_exif_orientation(img)
            assert out.size == (1920, 1080)

    def test_orientation_1_is_noop(self, temp_dir):
        path = create_oriented_image_file(temp_dir, 'o1.jpg', orientation=1)
        with Image.open(path) as img:
            out = ipro.apply_exif_orientation(img)
            assert out.size == (400, 200)


class TestResizeOrientation:
    """resize must auto-orient before stripping EXIF and measuring."""

    def test_resize_output_is_upright(self, iphone_portrait, temp_dir):
        out_dir = temp_dir / 'out'
        result = run_ipro('resize', iphone_portrait, '--width', '100',
                          '--output', out_dir)
        assert result.returncode == 0, result.stderr
        out = out_dir / 'IMG_5626.JPG'
        assert out.exists()
        _assert_portrait_red_on_top(out)

    def test_resize_width_applies_to_displayed_axis(self, iphone_portrait, temp_dir):
        out_dir = temp_dir / 'out'
        result = run_ipro('resize', iphone_portrait, '--width', '100',
                          '--output', out_dir)
        assert result.returncode == 0, result.stderr
        with Image.open(out_dir / 'IMG_5626.JPG') as img:
            assert img.size == (100, 200)

    def test_resize_height_applies_to_displayed_axis(self, iphone_portrait, temp_dir):
        out_dir = temp_dir / 'out'
        result = run_ipro('resize', iphone_portrait, '--height', '300',
                          '--output', out_dir)
        assert result.returncode == 0, result.stderr
        with Image.open(out_dir / 'IMG_5626.JPG') as img:
            assert img.size == (150, 300)

    def test_resize_upscale_check_uses_displayed_width(self, iphone_portrait, temp_dir):
        """Displayed width is 200, so 300 must be skipped as an upscale."""
        out_dir = temp_dir / 'out'
        result = run_ipro('resize', iphone_portrait, '--width', '300',
                          '--output', out_dir)
        assert result.returncode == 0
        assert 'Skipped 300px' in result.stdout
        assert not (out_dir / 'IMG_5626.JPG').exists()

    def test_resize_reports_displayed_dimensions(self, iphone_portrait, temp_dir):
        result = run_ipro('resize', iphone_portrait, '--width', '100',
                          '--output', temp_dir / 'out')
        assert '(200x400)' in result.stdout

    def test_resize_image_helper_auto_orients(self, iphone_portrait, temp_dir):
        created, skipped = ipro.resize_image(
            Path(iphone_portrait), temp_dir / 'out', [100, 150], dimension='width')
        assert [(f['width'], f['height']) for f in created] == [(100, 200), (150, 300)]
        for f in created:
            _assert_portrait_red_on_top(f['path'])


class TestConvertOrientation:
    """convert must auto-orient; with or without --strip-exif."""

    def test_convert_strip_exif_output_is_upright(self, iphone_portrait, temp_dir):
        out_dir = temp_dir / 'c-strip'
        result = run_ipro('convert', iphone_portrait, '--format', 'jpeg',
                          '--strip-exif', '--output', out_dir)
        assert result.returncode == 0, result.stderr
        out = out_dir / 'IMG_5626.jpg'
        _assert_portrait_red_on_top(out)
        assert _orientation_of(out) in (None, 1)

    def test_convert_preserving_exif_resets_orientation(self, iphone_portrait, temp_dir):
        """Pixels are rotated, so the tag must be reset to avoid double rotation."""
        out_dir = temp_dir / 'c-plain'
        result = run_ipro('convert', iphone_portrait, '--format', 'jpeg',
                          '--output', out_dir)
        assert result.returncode == 0, result.stderr
        out = out_dir / 'IMG_5626.jpg'
        _assert_portrait_red_on_top(out)
        assert _orientation_of(out) in (None, 1)

    def test_convert_preserving_exif_keeps_other_tags(self, temp_dir):
        make_tag = 0x010F
        src = create_oriented_image_file(temp_dir, 'cam.jpg', orientation=6,
                                         extra_exif={make_tag: 'Apple'})
        out_dir = temp_dir / 'c'
        result = run_ipro('convert', src, '--format', 'jpeg', '--output', out_dir)
        assert result.returncode == 0, result.stderr
        with Image.open(out_dir / 'cam.jpg') as img:
            assert img.getexif().get(make_tag) == 'Apple'

    @pytest.mark.parametrize('fmt,ext', [('png', '.png'), ('webp', '.webp')])
    def test_convert_to_other_formats_is_upright(self, iphone_portrait, temp_dir, fmt, ext):
        out_dir = temp_dir / fmt
        result = run_ipro('convert', iphone_portrait, '--format', fmt,
                          '--output', out_dir)
        assert result.returncode == 0, result.stderr
        _assert_portrait_red_on_top(out_dir / f'IMG_5626{ext}')

    def test_convert_image_helper_auto_orients(self, iphone_portrait, temp_dir):
        out = temp_dir / 'helper.jpg'
        assert ipro.convert_image(iphone_portrait, out, 'jpeg', strip_exif=True)
        _assert_portrait_red_on_top(out)


class TestInfoOrientation:
    """info must report displayed dimensions (PRD: honor EXIF orientation)."""

    def test_get_image_info_uses_displayed_dimensions(self, iphone_portrait):
        info = ipro.get_image_info(iphone_portrait)
        assert (info['width'], info['height']) == (200, 400)
        assert info['orientation'] == 'portrait'
        assert info['ratio_raw'] == '1:2'

    def test_info_cli_reports_portrait(self, iphone_portrait):
        result = run_ipro('info', iphone_portrait, '--short')
        assert result.returncode == 0, result.stderr
        fields = result.stdout.strip().split(',')
        assert fields[3:6] == ['200', '400', 'portrait']

    def test_info_unrotated_orientation_unchanged(self, temp_dir):
        path = create_oriented_image_file(temp_dir, 'o3.jpg', orientation=3)
        info = ipro.get_image_info(path)
        assert (info['width'], info['height']) == (400, 200)
        assert info['orientation'] == 'landscape'


class TestExtractOrientation:
    """extract writes frames without EXIF, so it must auto-orient too."""

    def test_extract_frame_is_upright(self, iphone_portrait, temp_dir):
        out_dir = temp_dir / 'ext'
        result = run_ipro('extract', iphone_portrait, '--output', out_dir)
        assert result.returncode == 0, result.stderr
        frames = sorted(out_dir.glob('*.jpg'))
        assert len(frames) == 1
        _assert_portrait_red_on_top(frames[0])


class TestChainOrientation:
    """The issue's pipeline: convert + resize must stay upright end to end."""

    def test_convert_then_resize_is_upright(self, iphone_portrait, temp_dir):
        result = run_ipro(
            'convert', iphone_portrait, '--format', 'jpeg', '--strip-exif',
            '--output', temp_dir / 'c',
            '+', 'resize', '--width', '100', '--output', temp_dir / 'r',
        )
        assert result.returncode == 0, result.stderr
        out = temp_dir / 'r' / 'IMG_5626.jpg'
        with Image.open(out) as img:
            assert img.size == (100, 200)
        _assert_portrait_red_on_top(out)
