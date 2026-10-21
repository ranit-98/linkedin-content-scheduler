import base64
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.api.routes.posts import get_post_image
from app.core.config import get_settings
from app.core.security import TokenCipher
from app.db.session import SessionLocal
from app.models import LinkedInConnection, PostStatus
from app.schemas.post import ScheduledPostCreate
from app.services.exceptions import LinkedInTemporaryError
from app.services.linkedin import LinkedInClient
from app.services.posts import IdempotencyConflictError, create_scheduled_post
from app.workers.tasks import publish_post


def _create_connection() -> LinkedInConnection:
    settings = get_settings()
    with SessionLocal() as db:
        connection = LinkedInConnection(
            linkedin_member_id="test-member",
            display_name="Test Member",
            access_token_encrypted=TokenCipher(settings.token_encryption_key).encrypt("token"),
            token_expires_at=datetime.now(UTC) + timedelta(days=1),
            scopes="openid profile w_member_social",
        )
        db.add(connection)
        db.commit()
        db.refresh(connection)
        db.expunge(connection)
        return connection


def _payload(connection_id: uuid.UUID, content: str = "Hello LinkedIn") -> ScheduledPostCreate:
    return ScheduledPostCreate(
        connection_id=connection_id,
        content=content,
        scheduled_at=datetime.now(UTC) - timedelta(seconds=1),
    )


def test_create_is_idempotent_and_worker_publishes() -> None:
    connection = _create_connection()
    key = uuid.uuid4()
    payload = _payload(connection.id)

    with SessionLocal() as db:
        first = create_scheduled_post(db, payload, key)
        repeated = create_scheduled_post(db, payload, key)
        post_id = first.id
        assert first.id == repeated.id

    assert publish_post(str(post_id)) == "published"
    assert publish_post(str(post_id)) == "skipped"

    with SessionLocal() as db:
        saved = db.get(type(first), post_id)
        assert saved is not None
        assert saved.status == PostStatus.PUBLISHED
        assert saved.linkedin_post_urn == f"urn:li:share:mock-{key}"


def test_temporary_failure_is_rescheduled_with_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = _create_connection()
    with SessionLocal() as db:
        post = create_scheduled_post(db, _payload(connection.id), uuid.uuid4())
        post_id = post.id

    def temporary_failure(*args: object, **kwargs: object) -> str:
        raise LinkedInTemporaryError("rate limited", retry_after_seconds=300)

    monkeypatch.setattr(LinkedInClient, "publish_text_post", temporary_failure)

    assert publish_post(str(post_id)) == "retry_scheduled"

    with SessionLocal() as db:
        saved = db.get(type(post), post_id)
        assert saved is not None
        assert saved.status == PostStatus.SCHEDULED
        assert saved.attempt_count == 1
        assert saved.last_error == "rate limited"
        next_attempt = saved.next_attempt_at.replace(tzinfo=UTC)
        assert next_attempt >= datetime.now(UTC) + timedelta(seconds=295)


def test_reusing_key_for_different_request_is_rejected() -> None:
    connection = _create_connection()
    key = uuid.uuid4()

    with SessionLocal() as db:
        create_scheduled_post(db, _payload(connection.id, "First"), key)
        with pytest.raises(IdempotencyConflictError):
            create_scheduled_post(db, _payload(connection.id, "Different"), key)


def test_scheduled_time_requires_timezone() -> None:
    with pytest.raises(ValidationError, match="timezone offset"):
        ScheduledPostCreate(
            connection_id=uuid.uuid4(),
            content="Hello",
            scheduled_at=datetime(2026, 10, 21, 10, 0),
        )


def test_image_is_validated_and_stored() -> None:
    connection = _create_connection()
    image = b"small-png-placeholder"
    payload = ScheduledPostCreate(
        connection_id=connection.id,
        content="Post with image",
        scheduled_at=datetime.now(UTC) + timedelta(minutes=5),
        image_base64=base64.b64encode(image).decode(),
        image_content_type="image/png",
        image_filename="update.png",
    )

    with SessionLocal() as db:
        post = create_scheduled_post(db, payload, uuid.uuid4())
        assert post.image_data == image
        assert post.has_image is True
        assert post.image_filename == "update.png"
        response = get_post_image(post.id, db)
        assert response.body == image
        assert response.media_type == "image/png"


def test_image_rejects_unsupported_content_type() -> None:
    with pytest.raises(ValidationError, match="JPEG, PNG, or GIF"):
        ScheduledPostCreate(
            connection_id=uuid.uuid4(),
            content="Unsupported image",
            scheduled_at=datetime.now(UTC) + timedelta(minutes=5),
            image_base64=base64.b64encode(b"image").decode(),
            image_content_type="image/webp",
            image_filename="image.webp",
        )
