"""Current authenticated user. Owner: Backend (A2)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(tags=["auth"])


class UserResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: str
    clerk_id: str | None = Field(default=None, alias="clerkId")
    email: str | None = None
    full_name: str | None = Field(default=None, alias="fullName")
    profile_image: str | None = Field(default=None, alias="profileImage")
    last_login_at: object | None = Field(default=None, alias="lastLoginAt")
    created_at: object = Field(alias="createdAt")
    updated_at: object | None = Field(default=None, alias="updatedAt")


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=user.id,
        clerkId=user.clerk_subject,
        email=user.email,
        fullName=user.full_name,
        profileImage=user.profile_image,
        lastLoginAt=user.last_login_at,
        createdAt=user.created_at,
        updatedAt=user.updated_at,
    )
