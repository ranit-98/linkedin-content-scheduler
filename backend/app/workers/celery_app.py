from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery("linkedin_scheduler", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "dispatch-due-linkedin-posts": {
            "task": "app.workers.tasks.dispatch_due_posts",
            "schedule": settings.scheduler_interval_seconds,
        }
    },
    task_routes={"app.workers.tasks.*": {"queue": "linkedin-publishing"}},
)
celery_app.autodiscover_tasks(["app.workers"])
