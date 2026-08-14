from datetime import datetime, timedelta, timezone

from course_alerts.deadline_alerts import DeadlineAlertRequest, dispatch_deadline_alert
from course_alerts.infrai_sms import SmsReceipt


class RecordingSms:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def send(self, *, to: str, body: str, idempotency_key: str) -> SmsReceipt:
        self.calls.append(
            {"to": to, "body": body, "idempotency_key": idempotency_key}
        )
        return SmsReceipt(message_id="msg_test_123", metadata={})


class RecordingInfrai:
    def __init__(self) -> None:
        self.sms = RecordingSms()


def request_due_in(now: datetime, hours: int, *, completed: bool = False) -> DeadlineAlertRequest:
    return DeadlineAlertRequest(
        course_id="algebra-2",
        course_title="Quadratic Functions",
        learner_id="learner-7",
        learner_name="Mina",
        learner_phone="+15555550123",
        deadline=now + timedelta(hours=hours),
        completed=completed,
    )


def test_sends_once_inside_deadline_window_and_reports_message_id() -> None:
    now = datetime(2026, 8, 14, 9, 0, tzinfo=timezone.utc)
    gateway = RecordingInfrai()

    report = dispatch_deadline_alert(request_due_in(now, 18), now=now, infrai=gateway)

    assert report.outcome == "sent"
    assert report.message_id == "msg_test_123"
    assert gateway.sms.calls == [
        {
            "to": "+15555550123",
            "body": "Hi Mina, Quadratic Functions is due 2026-08-15 at 03:00 UTC.",
            "idempotency_key": "deadline:algebra-2:learner-7:2026-08-15T03:00:00+00:00",
        }
    ]


def test_skips_completed_work_even_when_deadline_is_close() -> None:
    now = datetime(2026, 8, 14, 9, 0, tzinfo=timezone.utc)
    gateway = RecordingInfrai()

    report = dispatch_deadline_alert(
        request_due_in(now, 3, completed=True), now=now, infrai=gateway
    )

    assert report.outcome == "skipped_completed"
    assert gateway.sms.calls == []


def test_skips_deadline_outside_next_day() -> None:
    now = datetime(2026, 8, 14, 9, 0, tzinfo=timezone.utc)
    gateway = RecordingInfrai()

    report = dispatch_deadline_alert(request_due_in(now, 30), now=now, infrai=gateway)

    assert report.outcome == "skipped_outside_window"
    assert gateway.sms.calls == []
