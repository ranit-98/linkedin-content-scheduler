import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx

from app.core.config import Settings
from app.services.exceptions import LinkedInPermanentError, LinkedInTemporaryError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LinkedInToken:
    access_token: str
    expires_at: datetime
    scopes: str
    refresh_token: str | None = None
    refresh_token_expires_at: datetime | None = None


@dataclass(frozen=True)
class LinkedInProfile:
    member_id: str
    display_name: str | None


class LinkedInClient:
    AUTHORIZE_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
    POSTS_URL = "https://api.linkedin.com/rest/posts"
    IMAGES_URL = "https://api.linkedin.com/rest/images?action=initializeUpload"
    SCOPES = ("openid", "profile", "w_member_social")

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def authorization_url(self, state: str) -> str:
        query = urlencode(
            {
                "response_type": "code",
                "client_id": self.settings.linkedin_client_id,
                "redirect_uri": self.settings.linkedin_redirect_uri,
                "state": state,
                "scope": " ".join(self.SCOPES),
            }
        )
        return f"{self.AUTHORIZE_URL}?{query}"

    def exchange_code(self, code: str) -> LinkedInToken:
        try:
            response = httpx.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": self.settings.linkedin_client_id,
                    "client_secret": self.settings.linkedin_client_secret,
                    "redirect_uri": self.settings.linkedin_redirect_uri,
                },
                timeout=self.settings.publish_timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise LinkedInPermanentError("LinkedIn rejected the OAuth code exchange") from exc
        except httpx.RequestError as exc:
            raise LinkedInTemporaryError("LinkedIn OAuth service is unavailable") from exc

        payload = response.json()
        now = datetime.now(UTC)
        refresh_token = payload.get("refresh_token")
        refresh_expires_in = payload.get("refresh_token_expires_in")
        return LinkedInToken(
            access_token=payload["access_token"],
            expires_at=now + timedelta(seconds=int(payload["expires_in"])),
            scopes=payload.get("scope", " ".join(self.SCOPES)),
            refresh_token=refresh_token,
            refresh_token_expires_at=(
                now + timedelta(seconds=int(refresh_expires_in)) if refresh_expires_in else None
            ),
        )

    def get_profile(self, access_token: str) -> LinkedInProfile:
        try:
            response = httpx.get(
                self.USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=self.settings.publish_timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LinkedInPermanentError("Unable to read the LinkedIn member profile") from exc

        payload = response.json()
        return LinkedInProfile(member_id=payload["sub"], display_name=payload.get("name"))

    def publish_text_post(
        self,
        *,
        access_token: str,
        member_id: str,
        content: str,
        idempotency_key: uuid.UUID,
        image_data: bytes | None = None,
        image_content_type: str | None = None,
        image_filename: str | None = None,
    ) -> str:
        if self.settings.linkedin_mock_mode:
            return f"urn:li:share:mock-{idempotency_key}"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "LinkedIn-Version": self.settings.linkedin_api_version,
            "X-Restli-Protocol-Version": "2.0.0",
            # The database key is also sent for traceability across network retries.
            "X-RestLi-Idempotency-Key": str(idempotency_key),
        }
        payload = {
            "author": f"urn:li:person:{member_id}",
            "commentary": content,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }

        if image_data is not None:
            if image_content_type is None or image_filename is None:
                raise LinkedInPermanentError("Stored image metadata is incomplete")
            image_urn = self._upload_image(
                access_token=access_token,
                member_id=member_id,
                image_data=image_data,
                content_type=image_content_type,
            )
            payload["content"] = {"media": {"id": image_urn, "altText": image_filename}}

        try:
            response = httpx.post(
                self.POSTS_URL,
                headers=headers,
                json=payload,
                timeout=self.settings.publish_timeout_seconds,
            )
        except httpx.ConnectError as exc:
            raise LinkedInTemporaryError("Could not connect to LinkedIn") from exc
        except httpx.TimeoutException as exc:
            # A timeout is ambiguous, so an automatic retry could create a duplicate.
            raise LinkedInPermanentError(
                "LinkedIn response timed out; manual reconciliation is required"
            ) from exc
        except httpx.RequestError as exc:
            raise LinkedInTemporaryError("Temporary LinkedIn network error") from exc

        if response.status_code == 201:
            post_urn = response.headers.get("x-restli-id")
            if not post_urn:
                raise LinkedInPermanentError("LinkedIn created the post without returning its URN")
            return post_urn

        if response.status_code == 429 or 500 <= response.status_code < 600:
            retry_after = self._parse_retry_after(response.headers.get("Retry-After"))
            raise LinkedInTemporaryError(
                f"Temporary LinkedIn response ({response.status_code})",
                retry_after_seconds=retry_after,
            )

        logger.warning(
            "LinkedIn rejected publish request",
            extra={"status_code": response.status_code, "response": response.text[:500]},
        )
        raise LinkedInPermanentError(f"LinkedIn rejected the post ({response.status_code})")

    def _upload_image(
        self,
        *,
        access_token: str,
        member_id: str,
        image_data: bytes,
        content_type: str,
    ) -> str:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "LinkedIn-Version": self.settings.linkedin_api_version,
            "X-Restli-Protocol-Version": "2.0.0",
        }
        try:
            initialize = httpx.post(
                self.IMAGES_URL,
                headers=headers,
                json={"initializeUploadRequest": {"owner": f"urn:li:person:{member_id}"}},
                timeout=self.settings.publish_timeout_seconds,
            )
        except httpx.RequestError as exc:
            raise LinkedInTemporaryError("Could not initialize LinkedIn image upload") from exc

        if initialize.status_code == 429 or initialize.status_code >= 500:
            raise LinkedInTemporaryError(
                f"Temporary LinkedIn image initialization response ({initialize.status_code})",
                retry_after_seconds=self._parse_retry_after(initialize.headers.get("Retry-After")),
            )
        if initialize.status_code != 200:
            raise LinkedInPermanentError(
                f"LinkedIn rejected image initialization ({initialize.status_code})"
            )

        try:
            value = initialize.json()["value"]
            upload_url = value["uploadUrl"]
            image_urn = value["image"]
        except (KeyError, TypeError, ValueError) as exc:
            raise LinkedInPermanentError("LinkedIn returned invalid image upload details") from exc

        try:
            upload = httpx.put(
                upload_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": content_type,
                },
                content=image_data,
                timeout=self.settings.publish_timeout_seconds,
            )
        except httpx.RequestError as exc:
            raise LinkedInTemporaryError("Could not upload image bytes to LinkedIn") from exc

        if upload.status_code == 429 or upload.status_code >= 500:
            raise LinkedInTemporaryError(
                f"Temporary LinkedIn image upload response ({upload.status_code})",
                retry_after_seconds=self._parse_retry_after(upload.headers.get("Retry-After")),
            )
        if not 200 <= upload.status_code < 300:
            raise LinkedInPermanentError(
                f"LinkedIn rejected the image upload ({upload.status_code})"
            )
        return str(image_urn)

    @staticmethod
    def _parse_retry_after(value: str | None) -> int | None:
        if value and value.isdigit():
            return int(value)
        return None
