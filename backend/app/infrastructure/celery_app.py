"""Celery application and background jobs.

Jobs receive IDs (not objects) so they stay serializable and always read fresh data.
"""

import logging

from celery import Celery

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# No result backend: jobs are fire-and-forget, and a backend would add a second Redis
# dependency on the request path (it retried for ~19s when Redis was down).
celery_app = Celery("task_manager", broker=settings.redis_url)
celery_app.conf.update(
    task_always_eager=settings.celery_task_always_eager,
    task_acks_late=True,
    task_ignore_result=True,
    task_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    # Fail fast when the broker is down instead of blocking the HTTP request.
    broker_connection_timeout=2,
    broker_transport_options={"socket_connect_timeout": 2, "socket_timeout": 2},
)


@celery_app.task(name="notifications.task_assigned", autoretry_for=(Exception,), max_retries=3)
def notify_task_assigned(task_id: int, assignee_id: int) -> str:
    # In a real system this would send an email / push notification.
    message = f"Task {task_id} was assigned to user {assignee_id}"
    logger.info(message)
    return message


@celery_app.task(name="notifications.task_completed", autoretry_for=(Exception,), max_retries=3)
def notify_task_completed(task_id: int, owner_id: int) -> str:
    message = f"Task {task_id} was completed; notifying owner {owner_id}"
    logger.info(message)
    return message


class CeleryNotificationDispatcher:
    """Adapter for the NotificationDispatcher port.

    A broker outage must never break the HTTP request, so publishing errors are logged.
    """

    def task_assigned(self, task_id: int, assignee_id: int) -> None:
        self._send(notify_task_assigned, task_id, assignee_id)

    def task_completed(self, task_id: int, owner_id: int) -> None:
        self._send(notify_task_completed, task_id, owner_id)

    @staticmethod
    def _send(job: object, *args: int) -> None:
        try:
            job.apply_async(args=args, retry=False)  # type: ignore[attr-defined]
        except Exception:
            logger.exception("Could not enqueue background job %s", job)
