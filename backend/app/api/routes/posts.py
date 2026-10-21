import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import PostStatus, ScheduledPost
from app.schemas.post import ScheduledPostCreate, ScheduledPostRead
from app.services.posts import IdempotencyConflictError, create_scheduled_post

router = APIRouter()


@router.post("", response_model=ScheduledPostRead, status_code=status.HTTP_201_CREATED)
def schedule_post(
    payload: ScheduledPostCreate,
    db: Session = Depends(get_db),
    idempotency_key: uuid.UUID = Header(alias="Idempotency-Key"),
) -> ScheduledPost:
    try:
        return create_scheduled_post(db, payload, idempotency_key)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IdempotencyConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[ScheduledPostRead])
def list_posts(
    post_status: PostStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[ScheduledPost]:
    query = select(ScheduledPost).order_by(ScheduledPost.created_at.desc()).limit(limit)
    if post_status:
        query = query.where(ScheduledPost.status == post_status)
    return list(db.scalars(query))


@router.get("/{post_id}", response_model=ScheduledPostRead)
def get_post(post_id: uuid.UUID, db: Session = Depends(get_db)) -> ScheduledPost:
    post = db.get(ScheduledPost, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Scheduled post not found")
    return post


@router.get("/{post_id}/image", response_class=Response)
def get_post_image(post_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    post = db.get(ScheduledPost, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Scheduled post not found")
    if post.image_data is None or post.image_content_type is None:
        raise HTTPException(status_code=404, detail="Post image not found")
    return Response(
        content=post.image_data,
        media_type=post.image_content_type,
        headers={"Cache-Control": "private, max-age=300"},
    )
