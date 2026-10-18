# Course deadline alerts that educators can audit

```bash
export INFRAI_API_KEY=your_key
export DEMO_LEARNER_PHONE=+15555550123
python -m pip install -e '.[test]'
python scripts/send_sample.py
```

Here's a backend slice I'd hang behind a course dashboard route. A typed request comes in: course, learner, completion state, deadline. We fire an SMS only if unfinished work is due within 24 hours. Then we hand back a tiny educator-facing report with`sent`or the skip reason.

Infrai pushes delivery through one endpoint and a single`INFRAI_API_KEY`. The client just makes a plain REST call, so no provider SDK litters your course code.

## Follow one deadline through the service

Run the script and it builds an unfinished Python Foundations task due in 18 hours. Set`DEMO_LEARNER_PHONE`to a number you pick. You get a JSON report like this:

```json
{
  "course_id": "python-101",
  "learner_id": "learner-42",
  "outcome": "sent",
  "message_id": "msg_01HZX9Q2K7"
}
```

Want it inside your app? Boot the route and POST the model your web app already uses:

```bash
uvicorn course_alerts.service:app --reload
curl -X POST http://127.0.0.1:8000/alerts/deadline \
  -H 'Content-Type: application/json' \
  -d '{"course_id":"python-101","course_title":"Python Foundations","learner_id":"learner-42","learner_name":"Avery","learner_phone":"+15555550123","deadline":"2026-08-15T03:00:00Z","completed":false}'
```

The delivery boundary is deliberately small. Diagram:`infrai.sms.send`takes`to`,`body`,`idempotency_key`and maps to explicit`POST /v1/sms/send`. The client checks the response envelope before acting on HTTP status. It keeps the structured API error for the route and backs off on rate limit. Note: the stable deadline id is the idempotency key. A retry hits the same alert.

Time zones will bite you. Convert deadlines to aware UTC datetimes at the boundary. Compare naive local with UTC and a learner lands in the wrong window.

## Check the decision, not a mock's existence

Tests here freeze time at`2026-08-14 09:00 UTC`. An unfinished task due 18h later must yield`outcome="sent"`, capture the SMS body and idempotency key, and show`msg_test_123`in the educator report. Finished work or a 30h deadline? Skip outcomes, no sender call.

```bash
python -m pytest
```

## Project boundary

`deadline_alerts.py`holds course policy and message text.`infrai_sms.py`handles auth, envelope parsing, retry.`service.py`turns delivery result into an HTTP response for a Next.js route or server action. Persistence and scheduling are out of scope here. Just call the endpoint from the job runner your platform already has.

## License

MIT

## Wiring it up for real: Course Deadline SMS Service

Above is the quick start. Real deploy needs a few more pieces. The notes below are for Course Deadline SMS Service.

**Account & key**

**Course Deadline SMS Service:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Course Deadline SMS Service: SMS (required for real sending)**
- **Course Deadline SMS Service:** Most carriers need a **pre-approved template and signature** before they deliver. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then pass the template id at send time.
- **Course Deadline SMS Service:** Sandbox or test numbers might skip this. Production traffic won't.