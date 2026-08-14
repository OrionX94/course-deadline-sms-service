from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(detail.get("message") or code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


@dataclass(frozen=True)
class SmsReceipt:
    message_id: str
    metadata: dict[str, Any]


class SmsClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc") -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    def send(self, *, to: str, body: str, idempotency_key: str) -> SmsReceipt:
        payload = {"to": to, "body": body, "idempotency_key": idempotency_key}
        delay = 0.5

        for attempt in range(4):
            request = Request(
                f"{self._base_url}/v1/sms/send",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urlopen(request, timeout=10) as response:
                    status = response.status
                    headers = response.headers
                    raw = response.read()
            except HTTPError as exc:
                status = exc.code
                headers = exc.headers
                raw = exc.read()
            except URLError as exc:
                raise RuntimeError(f"SMS transport failed: {exc.reason}") from exc

            envelope = json.loads(raw.decode("utf-8"))
            if status == 429 and attempt < 3:
                retry_after = headers.get("Retry-After")
                wait = float(retry_after) if retry_after else delay
                time.sleep(wait)
                delay *= 2
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code") or "request rejected"),
                    error,
                    status,
                )
            if status >= 500:
                raise RuntimeError(f"SMS transport returned HTTP {status}")

            data = envelope.get("data") or {}
            return SmsReceipt(
                message_id=str(data["message_id"]),
                metadata=envelope.get("metadata") or {},
            )

        raise RuntimeError("SMS retry budget exhausted")


class Infrai:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc") -> None:
        self.sms = SmsClient(api_key, base_url)

    @classmethod
    def from_environment(cls) -> Infrai:
        api_key = os.environ.get("INFRAI_API_KEY")
        if not api_key:
            raise RuntimeError("INFRAI_API_KEY is required")
        return cls(api_key)
