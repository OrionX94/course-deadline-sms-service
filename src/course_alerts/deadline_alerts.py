from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError:
    BaseModel = None

from .infrai_sms import Infrai


if BaseModel is not None:
    class DeadlineAlertRequest(BaseModel):
        course_id: str = Field(min_length=1)
        course_title: str = Field(min_length=1)
        learner_id: str = Field(min_length=1)
        learner_name: str = Field(min_length=1)
        learner_phone: str = Field(min_length=8)
        deadline: datetime
        completed: bool


    class EducatorReport(BaseModel):
        course_id: str
        learner_id: str
        outcome: Literal["sent", "skipped_completed", "skipped_outside_window"]
        message_id: str | None = None
else:
    @dataclass(frozen=True)
    class DeadlineAlertRequest:
        course_id: str
        course_title: str
        learner_id: str
        learner_name: str
        learner_phone: str
        deadline: datetime
        completed: bool

        def __post_init__(self) -> None:
            for field_name in ("course_id", "course_title", "learner_id", "learner_name"):
                if not getattr(self, field_name):
                    raise ValueError(f"{field_name} must not be empty")
            if len(self.learner_phone) < 8:
                raise ValueError("learner_phone must contain at least 8 characters")


    @dataclass(frozen=True)
    class EducatorReport:
        course_id: str
        learner_id: str
        outcome: Literal["sent", "skipped_completed", "skipped_outside_window"]
        message_id: str | None = None


def dispatch_deadline_alert(
    request: DeadlineAlertRequest,
    *,
    now: datetime,
    infrai: Infrai,
) -> EducatorReport:
    if request.completed:
        return EducatorReport(
            course_id=request.course_id,
            learner_id=request.learner_id,
            outcome="skipped_completed",
        )

    deadline = request.deadline.astimezone(timezone.utc)
    current = now.astimezone(timezone.utc)
    hours_remaining = (deadline - current).total_seconds() / 3600
    if not 0 < hours_remaining <= 24:
        return EducatorReport(
            course_id=request.course_id,
            learner_id=request.learner_id,
            outcome="skipped_outside_window",
        )

    body = (
        f"Hi {request.learner_name}, {request.course_title} is due "
        f"{deadline:%Y-%m-%d at %H:%M UTC}."
    )
    key = f"deadline:{request.course_id}:{request.learner_id}:{deadline.isoformat()}"
    receipt = infrai.sms.send(
        to=request.learner_phone,
        body=body,
        idempotency_key=key,
    )
    return EducatorReport(
        course_id=request.course_id,
        learner_id=request.learner_id,
        outcome="sent",
        message_id=receipt.message_id,
    )
