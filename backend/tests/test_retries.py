from app.workers.tasks import retry_delay


def test_retry_delay_increases_exponentially() -> None:
    assert [retry_delay(attempt) for attempt in range(1, 5)] == [60, 120, 240, 480]


def test_retry_after_is_respected() -> None:
    assert retry_delay(attempt=1, retry_after=300) == 300
