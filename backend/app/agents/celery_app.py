"""Celery application configuration for MH-CyberScore agents.

Configures the Celery app with Redis broker, task routing per agent type,
scheduled beats for periodic rescanning, and timezone Europe/Paris.
"""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "mh_cyberscore",
    broker=settings.celery_broker_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    timezone="Europe/Paris",
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
    task_soft_time_limit=300,
    task_time_limit=600,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    task_routes={
        "app.agents.osint_agent.*": {"queue": "osint"},
        "app.agents.darkweb_agent.*": {"queue": "darkweb"},
        "app.agents.nthparty_agent.*": {"queue": "nthparty"},
        "app.agents.report_agent.*": {"queue": "reports"},
        "app.agents.chat_agent.*": {"queue": "chat"},
        "app.agents.alert_agent.*": {"queue": "default"},
        "app.agents.compliance_agent.*": {"queue": "default"},
        "app.agents.orchestrator.*": {"queue": "default"},
    },
    beat_schedule={
        "rescan-tier1-daily": {
            "task": "app.agents.orchestrator.rescan_tier",
            "schedule": crontab(hour=2, minute=0),
            "args": (1,),
        },
        "rescan-tier2-weekly": {
            "task": "app.agents.orchestrator.rescan_tier",
            "schedule": crontab(hour=3, minute=0, day_of_week="monday"),
            "args": (2,),
        },
        "rescan-tier3-monthly": {
            "task": "app.agents.orchestrator.rescan_tier",
            "schedule": crontab(hour=4, minute=0, day_of_month="1"),
            "args": (3,),
        },
    },
)

celery_app.autodiscover_tasks([
    "app.agents.orchestrator",
    "app.agents.osint_agent",
    "app.agents.darkweb_agent",
    "app.agents.nthparty_agent",
    "app.agents.chat_agent",
    "app.agents.report_agent",
    "app.agents.alert_agent",
    "app.agents.compliance_agent",
])
