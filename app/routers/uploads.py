from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.upload import ImageUploadResponse
from app.services.profile_images import (
    InvalidProfileImageError,
    MAX_UPLOAD_SIZE,
    get_profile_image_storage,
)

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/member-photo", response_model=ImageUploadResponse)
async def upload_member_photo(file: UploadFile = File(...)):
    content = await file.read(MAX_UPLOAD_SIZE + 1)

    try:
        storage = get_profile_image_storage()
        object_name, url = storage.upload_member_image(image_content=content)
    except InvalidProfileImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return ImageUploadResponse(object_name=object_name, url=url)
