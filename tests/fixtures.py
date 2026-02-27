"""Test fixtures for creating synthetic images with EXIF data."""

import io
from pathlib import Path
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS
import tempfile
import os


def create_test_image(width, height, color=(255, 0, 0), format='JPEG'):
    """
    Create a test image with specified dimensions.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        color: RGB tuple for image color
        format: Image format (JPEG, PNG, etc.)

    Returns:
        PIL Image object
    """
    img = Image.new('RGB', (width, height), color)
    return img


def create_image_with_exif(width, height, exif_data=None, color=(0, 255, 0)):
    """
    Create a test JPEG image with synthetic EXIF data.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        exif_data: Dictionary of EXIF tag names to values
        color: RGB tuple for image color

    Returns:
        bytes: JPEG image data with EXIF
    """
    img = Image.new('RGB', (width, height), color)

    # Create EXIF data if provided
    if exif_data:
        # Convert tag names to tag IDs
        exif_ifd = {}
        for tag_name, value in exif_data.items():
            # Find the tag ID for this tag name
            tag_id = None
            for id, name in TAGS.items():
                if name == tag_name:
                    tag_id = id
                    break

            if tag_id is not None:
                exif_ifd[tag_id] = value

        # Create EXIF bytes
        from PIL import Image as PILImage
        exif_bytes = PILImage.Exif()
        for tag_id, value in exif_ifd.items():
            exif_bytes[tag_id] = value

        # Save with EXIF
        output = io.BytesIO()
        img.save(output, format='JPEG', exif=exif_bytes)
        return output.getvalue()

    # Save without EXIF
    output = io.BytesIO()
    img.save(output, format='JPEG')
    return output.getvalue()


def save_test_image(image_bytes, directory=None, filename='test.jpg'):
    """
    Save image bytes to a temporary file.

    Args:
        image_bytes: Bytes of image data
        directory: Directory to save in (uses temp dir if None)
        filename: Filename to use

    Returns:
        Path: Path to saved file
    """
    if directory is None:
        directory = tempfile.gettempdir()

    filepath = Path(directory) / filename
    filepath.write_bytes(image_bytes)
    return filepath


def create_test_image_file(width, height, directory=None, filename='test.jpg',
                           exif_data=None, color=(0, 255, 0)):
    """
    Create and save a test image file with optional EXIF data.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        directory: Directory to save in (uses temp dir if None)
        filename: Filename to use
        exif_data: Dictionary of EXIF tag names to values
        color: RGB tuple for image color

    Returns:
        Path: Path to created file
    """
    image_bytes = create_image_with_exif(width, height, exif_data, color)
    return save_test_image(image_bytes, directory, filename)


# Common aspect ratios for testing
ASPECT_RATIOS = {
    'square': (1000, 1000),  # 1:1
    'landscape_4_3': (1200, 900),  # 4:3
    'landscape_3_2': (1500, 1000),  # 3:2
    'landscape_16_9': (1920, 1080),  # 16:9
    'landscape_instagram': (1910, 1000),  # 1.91:1
    'portrait_4_5': (1080, 1350),  # 4:5
    'portrait_9_16': (1080, 1920),  # 9:16
    'portrait_3_4': (900, 1200),  # 3:4
    'portrait_2_3': (1000, 1500),  # 2:3
    'landscape_5_4': (1250, 1000),  # 5:4
    'weird_ratio': (1234, 567),  # Non-standard ratio
}


# Sample EXIF data sets for testing
EXIF_DATA_FULL = {
    'DateTimeOriginal': '2024:11:12 14:30:00',
    'DateTime': '2024:11:12 14:30:00',
    'Make': 'Canon',
    'Model': 'Canon EOS 5D Mark IV',
    'Orientation': 1,
    'XResolution': (72, 1),
    'YResolution': (72, 1),
    'ResolutionUnit': 2,
    'Software': 'Adobe Lightroom',
    'Artist': 'Test Photographer',
}


EXIF_DATA_MINIMAL = {
    'DateTimeOriginal': '2024:11:12 14:30:00',
    'Make': 'Apple',
    'Model': 'iPhone 15 Pro',
}


EXIF_DATA_NO_DATE = {
    'Make': 'Sony',
    'Model': 'Alpha 7 IV',
    'Orientation': 1,
}


def create_mpo_file(directory, filename='test.mpo',
                    frame1_size=(800, 600), frame2_size=(800, 600),
                    frame1_color=(255, 0, 0), frame2_color=(0, 0, 255)):
    """
    Create a synthetic MPO (Multi-Picture Object) file with two frames.

    MPO files are JPEG-based containers with multiple images.
    Pillow can write MPO by saving a JPEG with append_images.

    Args:
        directory: Directory to save the file in
        filename: Output filename
        frame1_size: (width, height) of first frame
        frame2_size: (width, height) of second frame
        frame1_color: RGB color of first frame
        frame2_color: RGB color of second frame

    Returns:
        Path: Path to created MPO file
    """
    frame1 = Image.new('RGB', frame1_size, frame1_color)
    frame2 = Image.new('RGB', frame2_size, frame2_color)

    filepath = Path(directory) / filename
    frame1.save(filepath, format='MPO', save_all=True, append_images=[frame2])

    return filepath
