"""Tests for the rotate command (issue #23).

`ipro rotate <file> --degrees {90,180,270}` rotates clockwise in 90-degree
increments, writes to rotated/ (or --output) preserving the filename, and
participates in '+' command chaining.
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
    create_split_image_file,
    is_blue,
    is_red,
)

IPRO = str(Path(__file__).parent.parent / 'ipro.py')

MAKE_TAG = 0x010F
GPS_IFD_TAG = 0x8825


def run_ipro(*args):
    return subprocess.run(
        [sys.executable, IPRO] + [str(a) for a in args],
        capture_output=True,
        text=True,
    )


@pytest.fixture
def split_jpeg(temp_dir):
    """400x200 JPEG: left half red, right half blue, no EXIF."""
    return create_split_image_file(temp_dir, 'photo.jpg')


def _rgb(path):
    with Image.open(path) as img:
        return img.convert('RGB')


# ---------------------------------------------------------------------------
# Helper: rotate_image()
# ---------------------------------------------------------------------------

class TestRotateImageHelper:

    def test_rotate_90_is_clockwise(self, split_jpeg, temp_dir):
        out = temp_dir / 'out.jpg'
        result = ipro.rotate_image(split_jpeg, out, 90)
        assert result == (200, 400)
        img = _rgb(out)
        assert img.size == (200, 400)
        # Clockwise: the left (red) edge moves to the top
        assert is_red(img.getpixel((100, 50)))
        assert is_blue(img.getpixel((100, 350)))

    def test_rotate_180(self, split_jpeg, temp_dir):
        out = temp_dir / 'out.jpg'
        ipro.rotate_image(split_jpeg, out, 180)
        img = _rgb(out)
        assert img.size == (400, 200)
        assert is_red(img.getpixel((300, 100)))
        assert is_blue(img.getpixel((100, 100)))

    def test_rotate_270_is_counter_clockwise_90(self, split_jpeg, temp_dir):
        out = temp_dir / 'out.jpg'
        ipro.rotate_image(split_jpeg, out, 270)
        img = _rgb(out)
        assert img.size == (200, 400)
        # Left (red) edge moves to the bottom
        assert is_red(img.getpixel((100, 350)))
        assert is_blue(img.getpixel((100, 50)))

    @pytest.mark.parametrize('degrees', [0, 45, 360, -90, 91])
    def test_invalid_degrees_raise(self, split_jpeg, temp_dir, degrees):
        with pytest.raises(ValueError):
            ipro.rotate_image(split_jpeg, temp_dir / 'out.jpg', degrees)

    def test_rotation_is_relative_to_displayed_orientation(self, temp_dir):
        """An EXIF-oriented image is auto-oriented first, then rotated."""
        # Stored 400x200 with Orientation=6 displays 200x400, red on top
        src = create_oriented_image_file(temp_dir, 'iphone.jpg', orientation=6)
        out = temp_dir / 'out.jpg'
        ipro.rotate_image(src, out, 90)
        img = _rgb(out)
        # Displayed portrait rotated 90 CW -> landscape, red (top) moves right
        assert img.size == (400, 200)
        assert is_red(img.getpixel((300, 100)))
        with Image.open(out) as o:
            assert o.getexif().get(EXIF_ORIENTATION_TAG) in (None, 1)

    def test_preserves_exif_by_default(self, temp_dir):
        src = create_oriented_image_file(temp_dir, 'cam.jpg', orientation=1,
                                         extra_exif={MAKE_TAG: 'Apple'})
        out = temp_dir / 'out.jpg'
        ipro.rotate_image(src, out, 90)
        with Image.open(out) as img:
            assert img.getexif().get(MAKE_TAG) == 'Apple'

    def test_strip_exif(self, temp_dir):
        src = create_oriented_image_file(temp_dir, 'cam.jpg', orientation=1,
                                         extra_exif={MAKE_TAG: 'Apple'})
        out = temp_dir / 'out.jpg'
        ipro.rotate_image(src, out, 90, strip_exif=True)
        with Image.open(out) as img:
            assert MAKE_TAG not in img.getexif()

    def test_png_stays_png(self, temp_dir):
        src = create_split_image_file(temp_dir, 'g.png', format='PNG')
        out = temp_dir / 'g.png'.replace('g', 'h')
        ipro.rotate_image(src, out, 90)
        with Image.open(out) as img:
            assert img.format == 'PNG'
            assert img.size == (200, 400)

    def test_png_transparency_preserved(self, temp_dir):
        src = temp_dir / 'alpha.png'
        Image.new('RGBA', (40, 20), (255, 0, 0, 0)).save(src)
        out = temp_dir / 'alpha_out.png'
        ipro.rotate_image(src, out, 90)
        with Image.open(out) as img:
            assert img.mode == 'RGBA'
            assert img.getpixel((5, 5))[3] == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

class TestRotateCli:

    def test_rotate_command_exists(self):
        result = run_ipro('rotate', '--help')
        assert result.returncode == 0
        assert '--degrees' in result.stdout

    def test_rotate_default_output_dir_and_filename(self, split_jpeg, temp_dir):
        result = run_ipro('rotate', split_jpeg, '--degrees', '90')
        assert result.returncode == 0, result.stderr
        out = temp_dir / 'rotated' / 'photo.jpg'
        assert out.exists()
        assert _rgb(out).size == (200, 400)
        assert 'Created:' in result.stdout

    def test_rotate_custom_output(self, split_jpeg, temp_dir):
        out_dir = temp_dir / 'custom'
        result = run_ipro('rotate', split_jpeg, '--degrees', '180',
                          '--output', out_dir)
        assert result.returncode == 0, result.stderr
        assert (out_dir / 'photo.jpg').exists()

    def test_original_not_modified(self, split_jpeg):
        before = split_jpeg.read_bytes()
        run_ipro('rotate', split_jpeg, '--degrees', '90')
        assert split_jpeg.read_bytes() == before

    def test_degrees_required(self, split_jpeg):
        result = run_ipro('rotate', split_jpeg)
        assert result.returncode == ipro.EXIT_INVALID_ARGS

    @pytest.mark.parametrize('degrees', ['45', '0', '360', 'abc', '-90'])
    def test_invalid_degrees_rejected(self, split_jpeg, degrees):
        result = run_ipro('rotate', split_jpeg, '--degrees', degrees)
        assert result.returncode == ipro.EXIT_INVALID_ARGS

    def test_file_not_found(self, temp_dir):
        result = run_ipro('rotate', temp_dir / 'nope.jpg', '--degrees', '90')
        assert result.returncode == ipro.EXIT_FILE_NOT_FOUND

    def test_non_image_rejected(self, sample_non_image_file):
        result = run_ipro('rotate', sample_non_image_file, '--degrees', '90')
        assert result.returncode != 0

    def test_unsupported_format_rejected(self, temp_dir):
        src = temp_dir / 'pic.bmp'
        Image.new('RGB', (10, 10)).save(src, 'BMP')
        result = run_ipro('rotate', src, '--degrees', '90')
        assert result.returncode == ipro.EXIT_UNSUPPORTED_FORMAT
        assert 'convert' in result.stderr

    @pytest.mark.parametrize('quality', ['0', '101'])
    def test_invalid_quality(self, split_jpeg, quality):
        result = run_ipro('rotate', split_jpeg, '--degrees', '90',
                          '--quality', quality)
        assert result.returncode == ipro.EXIT_INVALID_ARGS

    def test_strip_exif_flag(self, temp_dir):
        src = create_oriented_image_file(temp_dir, 'cam.jpg', orientation=1,
                                         extra_exif={MAKE_TAG: 'Apple'})
        result = run_ipro('rotate', src, '--degrees', '90', '--strip-exif')
        assert result.returncode == 0, result.stderr
        with Image.open(temp_dir / 'rotated' / 'cam.jpg') as img:
            assert MAKE_TAG not in img.getexif()

    def test_path_traversal_rejected(self, split_jpeg):
        result = run_ipro('rotate', split_jpeg, '--degrees', '90',
                          '--output', '../../evil')
        assert result.returncode == ipro.EXIT_INVALID_ARGS


class TestRotateChaining:

    def test_resize_then_rotate(self, sample_landscape_image, temp_dir):
        result = run_ipro(
            'resize', sample_landscape_image, '--width', '300',
            '+', 'rotate', '--degrees', '90',
        )
        assert result.returncode == 0, result.stderr
        out = temp_dir / 'rotated' / 'landscape.jpg'
        assert out.exists()
        with Image.open(out) as img:
            assert img.size == (168, 300)

    def test_rotate_then_resize(self, split_jpeg, temp_dir):
        result = run_ipro(
            'rotate', split_jpeg, '--degrees', '90',
            '+', 'resize', '--width', '100',
        )
        assert result.returncode == 0, result.stderr
        out = temp_dir / 'resized-100w' / 'photo.jpg'
        with Image.open(out) as img:
            assert img.size == (100, 200)

    def test_rotated_dir_recognised_for_chaining(self):
        assert ipro.is_ipro_output_dir('rotated')


class TestRotateMultiFrame:

    def test_mpo_warns_only_primary_frame(self, sample_mpo_image, temp_dir):
        result = run_ipro('rotate', sample_mpo_image, '--degrees', '90')
        assert result.returncode == 0, result.stderr
        assert 'only the primary frame' in result.stderr
        out = temp_dir / 'rotated' / 'stereo.MPO'
        with Image.open(out) as img:
            assert img.format == 'JPEG'
            assert img.size == (600, 800)
