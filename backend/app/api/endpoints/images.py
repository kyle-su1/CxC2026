"""
Temporary image serving endpoint for SerpAPI Google Lens integration.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.services.image_hosting import get_temp_image_path

router = APIRouter()


@router.get("/temp/{image_id}")
async def get_temp_image(image_id: str):
    """
    Serve a temporarily stored image.
    Used by SerpAPI Google Lens to access uploaded images.
    """
    filepath = get_temp_image_path(image_id)
    
    if not filepath:
        raise HTTPException(status_code=404, detail="Image not found or expired")
    
    # Determine media type from extension
    if filepath.endswith(".png"):
        media_type = "image/png"
    elif filepath.endswith(".webp"):
        media_type = "image/webp"
    else:
        media_type = "image/jpeg"
    
    return FileResponse(filepath, media_type=media_type)
