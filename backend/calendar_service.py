import os
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]

class CalendarService:
    def __init__(self):
        # ✅ Read client config from environment
        client_secret_json = os.getenv("GOOGLE_CLIENT_SECRET_JSON")
        if not client_secret_json:
            raise ValueError("Missing GOOGLE_CLIENT_SECRET_JSON environment variable")

        # ✅ Load credentials from client config (no file read)
        flow = InstalledAppFlow.from_client_config(
            json.loads(client_secret_json),
            scopes=SCOPES
        )
        if os.getenv("RENDER") == "true":
    auth_url, _ = flow.authorization_url(prompt='consent')
    raise RuntimeError(
        f"Authorize this app by visiting this URL manually and running locally: {auth_url}"
    )
else:
    creds = flow.run_local_server(port=0)


        # ✅ Build calendar API service
        self.service = build("calendar", "v3", credentials=creds)

    def list_free_slots(self, start: datetime, end: datetime) -> List[Dict[str, str]]:
        """Return a list of free slots between `start` & `end` in ISO format."""

        start = start.replace(tzinfo=timezone.utc)
        end = end.replace(tzinfo=timezone.utc)

        body = {
            "timeMin": start.isoformat(),
            "timeMax": end.isoformat(),
            "timeZone": "UTC",
            "items": [{"id": "primary"}],
        }

        busy_resp = self.service.freebusy().query(body=body).execute()
        busy_periods = busy_resp["calendars"]["primary"]["busy"]

        free = []
        cursor = start
        for period in busy_periods:
            busy_start = datetime.fromisoformat(period["start"].replace("Z", "+00:00"))
            busy_end = datetime.fromisoformat(period["end"].replace("Z", "+00:00"))

            if cursor < busy_start:
                free.append({
                    "start": cursor.isoformat(),
                    "end": busy_start.isoformat()
                })

            cursor = max(cursor, busy_end)

        if cursor < end:
            free.append({
                "start": cursor.isoformat(),
                "end": end.isoformat()
            })

        return free

    def create_event(self, start: datetime, end: datetime, title: str) -> Dict[str, str]:
        """Insert an event and return its metadata."""

        start = start.replace(tzinfo=timezone.utc)
        end = end.replace(tzinfo=timezone.utc)

        event = {
            "summary": title,
            "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
        }

        created = (
            self.service
            .events()
            .insert(calendarId="primary", body=event)
            .execute()
        )

        return {
            "id": created["id"],
            "start": created["start"]["dateTime"],
            "end": created["end"]["dateTime"],
            "summary": created.get("summary", title),
        }
