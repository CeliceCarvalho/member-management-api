from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile

from app.database import get_db
from app.schemas.event import EventResponse
from app.schemas.member import MemberCreate, MemberResponse, MemberUpdate
from app.services import members as member_service
from app.services.profile_images import (
    InvalidProfileImageError,
    MAX_UPLOAD_SIZE,
    get_profile_image_storage,
)

router = APIRouter(prefix="/members", tags=["members"])


@router.post("/", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def create_member(request: Request, db: Session = Depends(get_db)):
    member_data = await build_member_create_from_request(request)
    return member_service.create_member(db, member_data)


async def build_member_create_from_request(request: Request) -> MemberCreate:
    content_type = request.headers.get("content-type", "")

    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        photo = form.get("photo") or form.get("file")
        photo_url = normalize_optional_form_value(form.get("photo_url"))

        if isinstance(photo, UploadFile):
            content = await photo.read(MAX_UPLOAD_SIZE + 1)

            try:
                storage = get_profile_image_storage()
                _, photo_url = storage.upload_member_image(image_content=content)
            except InvalidProfileImageError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(exc),
                ) from exc

        payload = {
            "name": form.get("name"),
            "tax_id": form.get("tax_id"),
            "birth_date": form.get("birth_date"),
            "phone": normalize_optional_form_value(form.get("phone")),
            "email": normalize_optional_form_value(form.get("email")),
            "photo_url": photo_url,
            "category": form.get("category"),
            "group_ids": [
                group_id for group_id in form.getlist("group_ids") if group_id
            ],
        }

        return validate_member_create(payload)

    return validate_member_create(await request.json())


def normalize_optional_form_value(value: object) -> object:
    if value == "":
        return None

    return value


def validate_member_create(payload: object) -> MemberCreate:
    try:
        return MemberCreate.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(),
        ) from exc


@router.get("/", response_model=list[MemberResponse])
def list_members(db: Session = Depends(get_db)):
    return member_service.list_members(db)


@router.get("/{member_id}", response_model=MemberResponse)
def get_member(member_id: UUID, db: Session = Depends(get_db)):
    return member_service.get_member(db, member_id)


@router.get("/{member_id}/events", response_model=list[EventResponse])
def list_member_attended_events(member_id: UUID, db: Session = Depends(get_db)):
    return member_service.list_member_attended_events(db, member_id)


@router.patch("/{member_id}", response_model=MemberResponse)
def update_member(member_id: UUID, member_data: MemberUpdate, db: Session = Depends(get_db)):
    return member_service.update_member(db, member_id, member_data)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(member_id: UUID, db: Session = Depends(get_db)):
    member_service.delete_member(db, member_id)
