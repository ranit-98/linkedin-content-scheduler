import uuid

import httpx

from app.core.config import Settings, get_settings
from app.services.linkedin import LinkedInClient


def test_mock_publish_returns_stable_urn() -> None:
    key = uuid.uuid4()
    client = LinkedInClient(get_settings())

    first = client.publish_text_post(
        access_token="token", member_id="member", content="Hello", idempotency_key=key
    )
    second = client.publish_text_post(
        access_token="token", member_id="member", content="Hello", idempotency_key=key
    )

    assert first == second == f"urn:li:share:mock-{key}"


def test_image_is_uploaded_before_post_creation(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    requests: list[tuple[str, dict[str, object]]] = []

    def fake_post(url: str, **kwargs: object) -> httpx.Response:
        requests.append((url, kwargs))
        if "images?action=initializeUpload" in url:
            return httpx.Response(
                200,
                json={
                    "value": {
                        "uploadUrl": "https://upload.example/image",
                        "image": "urn:li:image:test-image",
                    }
                },
            )
        return httpx.Response(201, headers={"x-restli-id": "urn:li:share:test-post"})

    def fake_put(url: str, **kwargs: object) -> httpx.Response:
        requests.append((url, kwargs))
        return httpx.Response(201)

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setattr(httpx, "put", fake_put)
    client = LinkedInClient(Settings(linkedin_mock_mode=False))

    result = client.publish_text_post(
        access_token="token",
        member_id="member",
        content="Hello with an image",
        idempotency_key=uuid.uuid4(),
        image_data=b"image-bytes",
        image_content_type="image/png",
        image_filename="launch.png",
    )

    assert result == "urn:li:share:test-post"
    assert requests[1][0] == "https://upload.example/image"
    post_payload = requests[2][1]["json"]
    assert isinstance(post_payload, dict)
    assert post_payload["content"] == {
        "media": {"id": "urn:li:image:test-image", "altText": "launch.png"}
    }
