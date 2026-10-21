from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import TokenCipher
from app.db.session import get_db
from app.models import LinkedInConnection
from app.schemas.connection import LinkedInConnectionRead

router = APIRouter()


@router.get("", response_model=list[LinkedInConnectionRead])
def list_connections(db: Session = Depends(get_db)) -> list[LinkedInConnection]:
    return list(db.scalars(select(LinkedInConnection).order_by(LinkedInConnection.created_at)))


@router.post("/mock", response_model=LinkedInConnectionRead, status_code=201)
def create_mock_connection(db: Session = Depends(get_db)) -> LinkedInConnection:
    settings = get_settings()
    if not settings.linkedin_mock_mode:
        raise HTTPException(status_code=404, detail="Not found")

    connection = db.scalar(
        select(LinkedInConnection).where(LinkedInConnection.linkedin_member_id == "mock-member")
    )
    if connection:
        return connection

    cipher = TokenCipher(settings.token_encryption_key)
    connection = LinkedInConnection(
        linkedin_member_id="mock-member",
        display_name="Demo LinkedIn Member",
        access_token_encrypted=cipher.encrypt("mock-token"),
        token_expires_at=datetime.now(UTC) + timedelta(days=365),
        scopes="openid profile w_member_social",
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)
    return connection
