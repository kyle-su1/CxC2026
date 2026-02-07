"""
Image cropping utilities for hybrid vision pipeline.
Uses PIL to crop detected objects from images based on bounding boxes.
"""
import io
from typing import Tuple
from PIL import Image


def crop_to_bounding_box(image_bytes: bytes, bbox: list, padding_percent: float = 0.05) -> bytes:
    """
    Crop an image to the specified bounding box with optional padding.
    
    Args:
        image_bytes: Raw image data
        bbox: [ymin, xmin, ymax, xmax] normalized to 0-1000
        padding_percent: Extra padding around the crop (0.05 = 5%)
        
    Returns:
        Cropped image as JPEG bytes
    """
    # Load image
    img = Image.open(io.BytesIO(image_bytes))
    width, height = img.size
    
    # Convert normalized coords (0-1000) to pixel coords
    ymin, xmin, ymax, xmax = bbox
    
    left = int((xmin / 1000) * width)
    top = int((ymin / 1000) * height)
    right = int((xmax / 1000) * width)
    bottom = int((ymax / 1000) * height)
    
    # Add padding
    pad_w = int((right - left) * padding_percent)
    pad_h = int((bottom - top) * padding_percent)
    
    left = max(0, left - pad_w)
    top = max(0, top - pad_h)
    right = min(width, right + pad_w)
    bottom = min(height, bottom + pad_h)
    
    # Crop
    cropped = img.crop((left, top, right, bottom))
    
    # Convert to bytes
    output = io.BytesIO()
    cropped.save(output, format='JPEG', quality=90)
    return output.getvalue()


def get_image_dimensions(image_bytes: bytes) -> Tuple[int, int]:
    """Get width and height of an image."""
    img = Image.open(io.BytesIO(image_bytes))
    return img.size
