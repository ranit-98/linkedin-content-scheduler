from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import TokenCipher, generate_oauth_state, hash_oauth_state
from app.db.session import get_db
from app.models import LinkedInConnection, OAuthState
from app.services.exceptions import LinkedInError
from app.services.linkedin import LinkedInClient

router = APIRouter()


@router.get(
    "/authorize", response_class=RedirectResponse, status_code=status.HTTP_307_TEMPORARY_REDIRECT
)
def authorize(db: Session = Depends(get_db)) -> RedirectResponse:
    settings = get_settings()
    settings.validate_secrets()
    raw_state = generate_oauth_state()
    db.add(
        OAuthState(
            state_hash=hash_oauth_state(raw_state),
            expires_at=datetime.now(UTC) + timedelta(minutes=settings.oauth_state_ttl_minutes),
        )
    )
    db.commit()
    return RedirectResponse(LinkedInClient(settings).authorization_url(raw_state))


@router.get("/callback", response_class=RedirectResponse)
def callback(
    code: str = Query(min_length=1),
    state: str = Query(min_length=1),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    settings = get_settings()
    now = datetime.now(UTC)
    oauth_state = db.scalar(
        select(OAuthState).where(
            OAuthState.state_hash == hash_oauth_state(state),
            OAuthState.used_at.is_(None),
            OAuthState.expires_at > now,
        )
    )
    if oauth_state is None:
        raise HTTPException(status_code=400, detail="OAuth state is invalid or expired")

    # Consume state before the network calls so a callback cannot be replayed.
    oauth_state.used_at = now
    db.commit()

    client = LinkedInClient(settings)
    try:
        token = client.exchange_code(code)
        profile = client.get_profile(token.access_token)
    except LinkedInError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    cipher = TokenCipher(settings.token_encryption_key)
    connection = db.scalar(
        select(LinkedInConnection).where(LinkedInConnection.linkedin_member_id == profile.member_id)
    )
    if connection is None:
        connection = LinkedInConnection(
            linkedin_member_id=profile.member_id,
            display_name=profile.display_name,
            access_token_encrypted=cipher.encrypt(token.access_token),
            refresh_token_encrypted=(
                cipher.encrypt(token.refresh_token) if token.refresh_token else None
            ),
            token_expires_at=token.expires_at,
            refresh_token_expires_at=token.refresh_token_expires_at,
            scopes=token.scopes,
        )
        db.add(connection)
    else:
        connection.display_name = profile.display_name
        connection.access_token_encrypted = cipher.encrypt(token.access_token)
        connection.refresh_token_encrypted = (
            cipher.encrypt(token.refresh_token) if token.refresh_token else None
        )
        connection.token_expires_at = token.expires_at
        connection.refresh_token_expires_at = token.refresh_token_expires_at
        connection.scopes = token.scopes
    db.commit()
    db.refresh(connection)

    query = urlencode({"linkedin": "connected", "connection_id": str(connection.id)})
    return RedirectResponse(f"{settings.frontend_url}?{query}")
