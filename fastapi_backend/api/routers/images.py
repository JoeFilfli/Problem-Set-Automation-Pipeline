"""
Image upload router - handles image uploads for submissions.
"""
import os
import uuid
import base64
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from api.dependencies import STORAGE_DIR

router = APIRouter(prefix="/api/py", tags=["images"])

# Create images directory
IMAGES_DIR = STORAGE_DIR / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


class ImageUploadRequest(BaseModel):
    image_data: str  # base64 encoded image with data URL prefix
    filename: str


@router.post("/images/upload")
def upload_image(payload: ImageUploadRequest) -> Dict[str, Any]:
    """
    Upload an image and return its ID.
    
    Args:
        payload: Image data and filename
        
    Returns:
        Image ID and URL
    """
    try:
        # Extract base64 data from data URL
        # Format: data:image/png;base64,iVBORw0KGgoAAAA...
        if not payload.image_data.startswith("data:image/"):
            raise HTTPException(status_code=400, detail="Invalid image data format")
        
        # Split to get the base64 part
        parts = payload.image_data.split(",", 1)
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid image data format")
        
        header = parts[0]  # data:image/png;base64
        base64_data = parts[1]
        
        # Extract image type from header
        # data:image/png;base64 -> png
        image_type = header.split("/")[1].split(";")[0]
        
        # Generate unique image ID
        image_id = f"img_{uuid.uuid4().hex[:16]}"
        filename = f"{image_id}.{image_type}"
        filepath = IMAGES_DIR / filename
        
        # Decode and save image
        image_bytes = base64.b64decode(base64_data)
        
        # Validate size (max 5MB)
        max_size = 5 * 1024 * 1024
        if len(image_bytes) > max_size:
            raise HTTPException(status_code=400, detail="Image size exceeds 5MB limit")
        
        # Validate that it's actually a valid image
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(image_bytes))
            img.verify()  # Verify it's a valid image
            # Re-open for potential format conversion (verify() closes the file)
            img = Image.open(io.BytesIO(image_bytes))
            
            # Check if image has reasonable dimensions
            width, height = img.size
            if width < 10 or height < 10:
                raise HTTPException(status_code=400, detail="Image dimensions too small (min 10x10)")
            if width > 10000 or height > 10000:
                raise HTTPException(status_code=400, detail="Image dimensions too large (max 10000x10000)")
                
        except HTTPException:
            raise
        except Exception as img_error:
            raise HTTPException(status_code=400, detail=f"Invalid image file: {str(img_error)}")
        
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        
        return {
            "success": True,
            "image_id": image_id,
            "filename": filename,
            "url": f"/api/py/images/{image_id}",
            "size": len(image_bytes)
        }
    except Exception as e:
        print(f"[API] Error uploading image: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/images/{image_id}")
def get_image(image_id: str) -> Response:
    """
    Retrieve an uploaded image.
    
    Args:
        image_id: Image identifier
        
    Returns:
        Image file
    """
    try:
        # Find image file with this ID
        matching_files = list(IMAGES_DIR.glob(f"{image_id}.*"))
        
        if not matching_files:
            raise HTTPException(status_code=404, detail=f"Image '{image_id}' not found")
        
        image_path = matching_files[0]
        
        # Determine content type from extension
        ext = image_path.suffix.lower()
        content_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".svg": "image/svg+xml"
        }
        content_type = content_types.get(ext, "application/octet-stream")
        
        # Read and return image
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        return Response(content=image_data, media_type=content_type)
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error retrieving image: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/images/{image_id}")
def delete_image(image_id: str) -> Dict[str, Any]:
    """
    Delete an uploaded image.
    
    Args:
        image_id: Image identifier
        
    Returns:
        Success status
    """
    try:
        # Find and delete image file
        matching_files = list(IMAGES_DIR.glob(f"{image_id}.*"))
        
        if not matching_files:
            raise HTTPException(status_code=404, detail=f"Image '{image_id}' not found")
        
        for file_path in matching_files:
            file_path.unlink()
        
        return {
            "success": True,
            "message": f"Image '{image_id}' deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error deleting image: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))
