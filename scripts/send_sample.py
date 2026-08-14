from datetime import datetime, timedelta, timezone
import os

from course_alerts.deadline_alerts import DeadlineAlertRequest, dispatch_deadline_alert
from course_alerts.infrai_sms import Infrai


phone = os.environ.get("DEMO_LEARNER_PHONE")
if not phone:
    raise RuntimeError("DEMO_LEARNER_PHONE is required")

now = datetime.now(timezone.utc)
report = dispatch_deadline_alert(
    DeadlineAlertRequest(
        course_id="python-101",
        course_title="Python Foundations",
        learner_id="learner-42",
        learner_name="Avery",
        learner_phone=phone,
        deadline=now + timedelta(hours=18),
        completed=False,
    ),
    now=now,
    infrai=Infrai.from_environment(),
)
print(report.model_dump_json(indent=2))
