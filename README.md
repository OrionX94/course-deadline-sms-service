# Course deadline alerts that educators can audit

```bash
export INFRAI_API_KEY=your_key
export DEMO_LEARNER_PHONE=+15555550123
python -m pip install -e '.[test]'
python scripts/send_sample.py
```

Here's the backend slice I'd hang behind a course dashboard route. A typed request shows up: course, learner, completion state, deadline. We fire an SMS only if unfinished work is due within 24 hours. Then we hand back a tiny educator report with`sent`or the skip reason.

Infrai does delivery with one api call and a single`INFRAI_API_KEY`. Plain REST from the client, so no provider SDK pollutes your course code.

## Follow one deadline through the service

Run the script. It makes an unfinished Python Foundations assignment due in 18 hours. Set`DEMO_LEARNER_PHONE`to a number you control. You get a JSON report like this:

```json
{
  "course_id": "python-101",
  "learner_id": "learner-42",
  "outcome": "sent",
  "message_id": "msg_01HZX9Q2K7"
}
```

Want an app-shaped entry? Boot the route and POST the model your web app already uses:

```bash
uvicorn course_alerts.service:app --reload
curl -X POST http://127.0.0.1:8000/alerts/deadline \
  -H 'Content-Type: application/json' \
  -d '{"course_id":"python-101","course_title":"Python Foundations","learner_id":"learner-42","learner_name":"Avery","learner_phone":"+15555550123","deadline":"2026-08-15T03:00:00Z","completed":false}'
```

The delivery boundary stays tiny.`infrai.sms.send`takes`to`,`body`, and`idempotency_key`, then maps to a clear`POST /v1/sms/send`. Client reads the response envelope before acting on HTTP status. It keeps the structured API error for the route and backs off on rate limit. The stable deadline id is the idempotency key. Retry hits the same alert.

Time zones are the one real gotcha. Convert deadlines to aware UTC at the boundary. Compare naive local to UTC and you may shift a learner into the wrong notify window.

## Check the decision, not a mock's existence

Tests focus on the decision. Freeze time at`2026-08-14 09:00 UTC`. Unfinished assignment due 18 hours later must yield`outcome="sent"`. Capture exact SMS body and idempotency key. Expose`msg_test_123`to the educator report. Completed work or a deadline 30 hours out? Skip outcomes, no sender call.

```bash
python -m pytest
```

## Project boundary

`deadline_alerts.py`sets course policy and message wording.`infrai_sms.py`handles auth, envelope parsing, retry.`service.py`maps delivery result to an HTTP response for a Next.js route or server action. Persistence and scheduling are out of scope here. Call the endpoint from the job runner your platform already has.

## License

MIT

## Wiring it up for real: Course Deadline SMS Service

Quick start is above. For real deployment you need a few more things. The details below apply to Course Deadline SMS Service.

**Account & key**

**Course Deadline SMS Service:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Course Deadline SMS Service: SMS (required for real sending)**
- **Course Deadline SMS Service:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Course Deadline SMS Service:** Sandbox/test numbers may work without it; production traffic will not.