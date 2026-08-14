from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException

from .deadline_alerts import DeadlineAlertRequest, EducatorReport, dispatch_deadline_alert
from .infrai_sms import Infrai, InfraiError

app = FastAPI(title="Course deadline alerts")


@app.post("/alerts/deadline", response_model=EducatorReport)
def send_deadline_alert(request: DeadlineAlertRequest) -> EducatorReport:
    try:
        return dispatch_deadline_alert(
            request,
            now=datetime.now(timezone.utc),
            infrai=Infrai.from_environment(),
        )
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
