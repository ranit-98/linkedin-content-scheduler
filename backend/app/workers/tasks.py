import logging
import uuid
from datetime import UTC, datetime, timedelta

from celery import shared_task
from sqlalchemy import select, update

from app.core.config import get_settings
from app.core.security import TokenCipher
from app.db.session import SessionLocal
from app.models import LinkedInConnection, PostStatus, ScheduledPost
from app.services.exceptions import LinkedInPermanentError, LinkedInTemporaryError
from app.services.linkedin import LinkedInClient

logger = logging.getLogger(__name__)


def retry_delay(attempt: int, retry_after: int | None = None) -> int:
    settings = get_settings()
    exponential = min(
        settings.retry_base_delay_seconds * (2 ** max(attempt - 1, 0)),
        settings.retry_max_delay_seconds,
    )
    return max(exponential, retry_after or 0)


@shared_task(name="app.workers.tasks.dispatch_due_posts")
def dispatch_due_posts() -> int:
    now = datetime.now(UTC)
    stale_before = now - timedelta(minutes=get_settings().processing_timeout_minutes)
    with SessionLocal() as db:
        # A worker may die after LinkedIn accepted a request. Fail stale claims for manual
        # reconciliation instead of retrying an outcome that is no longer knowable.
        db.execute(
            update(ScheduledPost)
            .where(
                ScheduledPost.status == PostStatus.PROCESSING,
                ScheduledPost.processing_started_at < stale_before,
            )
            .values(
                status=PostStatus.FAILED,
                last_error="Publishing worker was interrupted; manual reconciliation required",
                processing_started_at=None,
            )
        )
        db.commit()
        post_ids = list(
            db.scalars(
                select(ScheduledPost.id)
                .where(
                    ScheduledPost.status == PostStatus.SCHEDULED,
                    ScheduledPost.next_attempt_at <= now,
                )
                .order_by(ScheduledPost.next_attempt_at)
                .limit(100)
            )
        )

    from app.workers.celery_app import celery_app

    for post_id in post_ids:
        celery_app.send_task("app.workers.tasks.publish_post", args=[str(post_id)])
    if post_ids:
        logger.info("Dispatched due posts", extra={"count": len(post_ids)})
    return len(post_ids)


@shared_task(name="app.workers.tasks.publish_post")
def publish_post(post_id: str) -> str:
    parsed_id = uuid.UUID(post_id)
    now = datetime.now(UTC)

    with SessionLocal() as db:
        # Atomic status transition is the concurrency gate. Duplicate queue messages become no-ops.
        claimed = db.execute(
            update(ScheduledPost)
            .where(
                ScheduledPost.id == parsed_id,
                ScheduledPost.status == PostStatus.SCHEDULED,
                ScheduledPost.next_attempt_at <= now,
            )
            .values(
                status=PostStatus.PROCESSING,
                processing_started_at=now,
                attempt_count=ScheduledPost.attempt_count + 1,
                last_error=None,
            )
            .returning(ScheduledPost.id)
        ).scalar_one_or_none()
        db.commit()
        if claimed is None:
            return "skipped"

        post = db.get(ScheduledPost, parsed_id)
        connection = db.get(LinkedInConnection, post.connection_id) if post else None
        if post is None or connection is None:
            logger.error("Post or LinkedIn connection disappeared", extra={"post_id": post_id})
            if post:
                post.status = PostStatus.FAILED
                post.last_error = "LinkedIn connection no longer exists"
                post.processing_started_at = None
                db.commit()
            return "missing"

        settings = get_settings()
        try:
            access_token = TokenCipher(settings.token_encryption_key).decrypt(
                connection.access_token_encrypted
            )
            post_urn = LinkedInClient(settings).publish_text_post(
                access_token=access_token,
                member_id=connection.linkedin_member_id,
                content=post.content,
                idempotency_key=post.idempotency_key,
                image_data=post.image_data,
                image_content_type=post.image_content_type,
                image_filename=post.image_filename,
            )
        except LinkedInTemporaryError as exc:
            if post.attempt_count >= post.max_attempts:
                post.status = PostStatus.FAILED
                result = "failed"
            else:
                delay = retry_delay(post.attempt_count, exc.retry_after_seconds)
                post.status = PostStatus.SCHEDULED
                post.next_attempt_at = datetime.now(UTC) + timedelta(seconds=delay)
                result = "retry_scheduled"
            post.last_error = str(exc)
            post.processing_started_at = None
            db.commit()
            logger.warning(
                "Temporary LinkedIn publish failure",
                extra={"post_id": post_id, "attempt": post.attempt_count, "result": result},
            )
            return result
        except (LinkedInPermanentError, ValueError) as exc:
            post.status = PostStatus.FAILED
            post.last_error = str(exc)
            post.processing_started_at = None
            db.commit()
            logger.error("LinkedIn post failed permanently", extra={"post_id": post_id})
            return "failed"
        except Exception:
            post.status = PostStatus.FAILED
            post.last_error = "Unexpected internal publishing error"
            post.processing_started_at = None
            db.commit()
            logger.exception("Unexpected LinkedIn publish error", extra={"post_id": post_id})
            return "failed"

        post.status = PostStatus.PUBLISHED
        post.linkedin_post_urn = post_urn
        post.published_at = datetime.now(UTC)
        post.processing_started_at = None
        db.commit()
        logger.info("LinkedIn post published", extra={"post_id": post_id, "post_urn": post_urn})
        return "published"
