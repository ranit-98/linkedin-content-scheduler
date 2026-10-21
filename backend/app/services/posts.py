import base64
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import LinkedInConnection, ScheduledPost
from app.schemas.post import ScheduledPostCreate


class IdempotencyConflictError(Exception):
    pass


def _same_instant(left: datetime, right: datetime) -> bool:
    """SQLite drops offsets in tests; production PostgreSQL keeps timezone-aware values."""
    if left.tzinfo is None:
        left = left.replace(tzinfo=UTC)
    if right.tzinfo is None:
        right = right.replace(tzinfo=UTC)
    return left.astimezone(UTC) == right.astimezone(UTC)


def create_scheduled_post(
    db: Session,
    payload: ScheduledPostCreate,
    idempotency_key: uuid.UUID,
) -> ScheduledPost:
    connection = db.get(LinkedInConnection, payload.connection_id)
    if connection is None:
        raise LookupError("LinkedIn connection not found")

    image_data = base64.b64decode(payload.image_base64) if payload.image_base64 else None
    existing = db.scalar(
        select(ScheduledPost).where(ScheduledPost.idempotency_key == idempotency_key)
    )
    if existing:
        same_request = (
            existing.connection_id == payload.connection_id
            and existing.content == payload.content
            and existing.image_data == image_data
            and existing.image_content_type == payload.image_content_type
            and existing.image_filename == payload.image_filename
            and _same_instant(existing.scheduled_at, payload.scheduled_at)
        )
        if not same_request:
            raise IdempotencyConflictError("Idempotency key was already used for another request")
        return existing

    post = ScheduledPost(
        connection_id=payload.connection_id,
        content=payload.content,
        image_data=image_data,
        image_content_type=payload.image_content_type,
        image_filename=payload.image_filename,
        scheduled_at=payload.scheduled_at,
        next_attempt_at=max(payload.scheduled_at, datetime.now(UTC)),
        max_attempts=payload.max_attempts,
        idempotency_key=idempotency_key,
    )
    db.add(post)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(ScheduledPost).where(ScheduledPost.idempotency_key == idempotency_key)
        )
        if existing:
            return existing
        raise
    db.refresh(post)
    return post
