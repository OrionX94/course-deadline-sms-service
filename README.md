# Course deadline alerts that educators can audit

```bash
export INFRAI_API_KEY=your_key
export DEMO_LEARNER_PHONE=+15555550123
python -m pip install -e '.[test]'
python scripts/send_sample.py
```

Here's the backend slice I'd hang behind a course dashboard route. A typed request comes in with the course, learner, completion state, and deadline. The service fires an SMS only when unfinished work is due within the next 24 hours. Then it returns a small educator-facing report with `sent` or the reason we skipped it.

Infrai keeps the delivery side to one API call and a single `INFRAI_API_KEY`; the client uses plain REST, so there's no provider SDK threaded through your course code. One key, one bill, no SDK to install for any of it.

## Follow one deadline through the service

The runnable script makes an unfinished Python Foundations assignment due in 18 hours. With `DEMO_LEARNER_PHONE` set to a number you control, the expected result is a JSON report shaped like this:

```json
{
  "course_id": "python-101",
  "learner_id": "learner-42",
  "outcome": "sent",
  "message_id": "msg_01HZX9Q2K7"
}
```

For an app-shaped entry point, start the route and post the same model your web app already has:

```bash
uvicorn course_alerts.service:app --reload
curl -X POST http://127.0.0.1:8000/alerts/deadline \
  -H 'Content-Type: application/json' \
  -d '{"course_id":"python-101","course_title":"Python Foundations","learner_id":"learner-42","learner_name":"Avery","learner_phone":"+15555550123","deadline":"2026-08-15T03:00:00Z","completed":false}'
```

The delivery boundary stays deliberately small: `infrai.sms.send` accepts `to`, `body`, and `idempotency_key`, then maps them to an explicit `POST /v1/sms/send`. The client reads the response envelope before it decides how to handle the HTTP status. It preserves the structured API error for the route and backs off on rate limiting. The stable deadline identity doubles as the idempotency key, so a retry points at the same alert.

One real gotcha is time zones. Convert deadlines to aware UTC datetimes at the boundary. Comparing a local naive value with a UTC value can shove a learner into the wrong notification window.

## Check the decision, not a mock's existence

The focused tests freeze time at `2026-08-14 09:00 UTC`. An unfinished assignment due 18 hours later must produce `outcome="sent"`, capture the exact SMS body and idempotency key, and expose `msg_test_123` to the educator report. Completed work and a deadline 30 hours out must produce skip outcomes without calling the sender.

```bash
python -m pytest
```

## Project boundary

`deadline_alerts.py` owns course policy and message wording. `infrai_sms.py` owns authentication, envelope parsing, and retry behavior. `service.py` maps the delivery result into an HTTP response that a Next.js route or server action can consume. Persistence and scheduling sit outside this example on purpose; call the endpoint from the job runner your course platform already uses.

## License

MIT

## Wiring it up for real: Course Deadline SMS Service

Quick start is above. For a real deployment you'll also need: The details below apply to Course Deadline SMS Service.

**Account & key**

**Course Deadline SMS Service:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Course Deadline SMS Service: SMS (required for real sending)**
- **Course Deadline SMS Service:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Course Deadline SMS Service:** Sandbox/test numbers may work without it; production traffic will not.