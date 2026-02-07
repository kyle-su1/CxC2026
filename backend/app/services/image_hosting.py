"""
Temporary image hosting service for SerpAPI Google Lens integration.
Stores images temporarily and serves them via public URLs.
"""
import os
import uuid
import time
import threading
from pathlib import Path

from app.core.config import settings

# Storage directory inside container
TEMP_IMAGE_DIR = Path("/app/temp_images")
TEMP_IMAGE_DIR.mkdir(exist_ok=True)

# TTL for temporary images (5 minutes)
IMAGE_TTL_SECONDS = 300

# Track stored images for cleanup
_stored_images = {}


def cleanup_expired_images():
    """Remove images older than TTL."""
    current_time = time.time()
    expired = [
        img_id for img_id, data in _stored_images.items()
        if current_time - data["timestamp"] > IMAGE_TTL_SECONDS
    ]
    for img_id in expired:
        try:
            os.remove(_stored_images[img_id]["path"])
        except:
            pass
        _stored_images.pop(img_id, None)


def store_temp_image(image_bytes: bytes, extension: str = "jpg") -> str:
    """
    Store image bytes temporarily and return the image ID.
    
    Args:
        image_bytes: Raw image data
        extension: File extension (jpg, png, webp)
        
    Returns:
        Image ID (use with get_temp_image_url)
    """
    cleanup_expired_images()
    
    image_id = str(uuid.uuid4())
    filename = f"{image_id}.{extension}"
    filepath = TEMP_IMAGE_DIR / filename
    
    with open(filepath, "wb") as f:
        f.write(image_bytes)
    
    _stored_images[image_id] = {
        "path": str(filepath),
        "timestamp": time.time(),
        "extension": extension
    }
    
    return image_id


def get_temp_image_path(image_id: str) -> str | None:
    """Get the file path for a stored image."""
    if image_id in _stored_images:
        return _stored_images[image_id]["path"]
    
    # Check if file exists even if not in memory (server restart)
    for ext in ["jpg", "png", "webp", "jpeg"]:
        path = TEMP_IMAGE_DIR / f"{image_id}.{ext}"
        if path.exists():
            return str(path)
    
    return None


def get_public_image_url(image_id: str, base_url: str | None = None) -> str:
    """
    Get the public URL for a stored image.
    
    Args:
        image_id: The ID returned by store_temp_image
        base_url: Override base URL (defaults to PUBLIC_BASE_URL env var)
        
    Returns:
        Public URL like https://xxxx.ngrok.io/api/v1/images/temp/{image_id}
    """
    url_base = base_url or settings.PUBLIC_BASE_URL
    return f"{url_base}/api/v1/images/temp/{image_id}"
