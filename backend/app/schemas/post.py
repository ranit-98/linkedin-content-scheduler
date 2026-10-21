import base64
import binascii
import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.scheduled_post import PostStatus


class ScheduledPostCreate(BaseModel):
    connection_id: uuid.UUID
    content: str = Field(min_length=1, max_length=3000)
    scheduled_at: datetime
    max_attempts: int = Field(default=5, ge=1, le=10)
    image_base64: str | None = None
    image_content_type: str | None = None
    image_filename: str | None = Field(default=None, max_length=255)

    @field_validator("content")
    @classmethod
    def reject_blank_content(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Post content cannot be blank")
        return cleaned

    @field_validator("scheduled_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("scheduled_at must include a timezone offset")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_image(self) -> "ScheduledPostCreate":
        image_fields = (self.image_base64, self.image_content_type, self.image_filename)
        if not any(image_fields):
            return self
        if not all(image_fields):
            raise ValueError("Image data, content type, and filename must be provided together")
        if self.image_content_type not in {"image/jpeg", "image/png", "image/gif"}:
            raise ValueError("Image must be a JPEG, PNG, or GIF")
        try:
            image = base64.b64decode(self.image_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("Image data is not valid base64") from exc
        if not image:
            raise ValueError("Image cannot be empty")
        if len(image) > 5 * 1024 * 1024:
            raise ValueError("Image must be 5 MB or smaller")
        return self


class ScheduledPostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    connection_id: uuid.UUID
    content: str
    has_image: bool
    image_filename: str | None
    scheduled_at: datetime
    next_attempt_at: datetime
    status: PostStatus
    attempt_count: int
    max_attempts: int
    idempotency_key: uuid.UUID
    linkedin_post_urn: str | None
    last_error: str | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
