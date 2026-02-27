"""Pytest configuration and shared fixtures."""

import pytest
import tempfile
import shutil
from pathlib import Path
from .fixtures import (
    create_test_image_file,
    create_mpo_file,
    ASPECT_RATIOS,
    EXIF_DATA_FULL,
    EXIF_DATA_MINIMAL,
    EXIF_DATA_NO_DATE,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    # Cleanup after test
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def sample_square_image(temp_dir):
    """Create a 1000x1000 (1:1) test image."""
    width, height = ASPECT_RATIOS['square']
    return create_test_image_file(
        width, height,
        directory=temp_dir,
        filename='square.jpg',
        color=(255, 0, 0)
    )


@pytest.fixture
def sample_landscape_image(temp_dir):
    """Create a 1920x1080 (16:9) landscape test image."""
    width, height = ASPECT_RATIOS['landscape_16_9']
    return create_test_image_file(
        width, height,
        directory=temp_dir,
        filename='landscape.jpg',
        color=(0, 255, 0)
    )


@pytest.fixture
def sample_portrait_image(temp_dir):
    """Create a 1080x1920 (9:16) portrait test image."""
    width, height = ASPECT_RATIOS['portrait_9_16']
    return create_test_image_file(
        width, height,
        directory=temp_dir,
        filename='portrait.jpg',
        color=(0, 0, 255)
    )


@pytest.fixture
def sample_image_with_exif(temp_dir):
    """Create a test image with full EXIF data."""
    width, height = ASPECT_RATIOS['landscape_4_3']
    return create_test_image_file(
        width, height,
        directory=temp_dir,
        filename='with_exif.jpg',
        exif_data=EXIF_DATA_FULL,
        color=(255, 255, 0)
    )


@pytest.fixture
def sample_image_no_exif(temp_dir):
    """Create a test image without EXIF data."""
    width, height = ASPECT_RATIOS['landscape_3_2']
    return create_test_image_file(
        width, height,
        directory=temp_dir,
        filename='no_exif.jpg',
        exif_data=None,
        color=(255, 0, 255)
    )


@pytest.fixture
def sample_non_image_file(temp_dir):
    """Create a non-image file (text file) for testing error handling."""
    filepath = temp_dir / 'not_an_image.jpg'
    filepath.write_text('This is not an image file')
    return filepath


@pytest.fixture
def sample_png_image(temp_dir):
    """Create a PNG image for format testing."""
    from PIL import Image
    img = Image.new('RGB', (800, 600), (128, 128, 128))
    filepath = temp_dir / 'test.png'
    img.save(filepath, 'PNG')
    return filepath


@pytest.fixture
def sample_mpo_image(temp_dir):
    """Create a synthetic MPO image with 2 frames for format testing."""
    return create_mpo_file(
        temp_dir,
        filename='stereo.MPO',
        frame1_size=(800, 600),
        frame2_size=(800, 600),
        frame1_color=(255, 0, 0),
        frame2_color=(0, 0, 255),
    )
