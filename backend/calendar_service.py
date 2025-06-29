# backend/calendar_service.py

import os
import pickle
from datetime import datetime, timedelta, timezone  # ✅ Add timezone
from typing import List, Dict

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class CalendarService:
    def __init__(self):
        # Path to OAuth 2.0 client secrets
        cred_path = os.getenv(
            "GOOGLE_OAUTH_CLIENT_SECRET",
            os.path.join(os.getcwd(), "credentials", "client_secret.json")
        )
        token_path = os.path.join(os.getcwd(), "credentials", "token.pickle")

        creds = None
        if os.path.exists(token_path):
            with open(token_path, "rb") as token_file:
                creds = pickle.load(token_file)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, "wb") as token_file:
                pickle.dump(creds, token_file)

        self.service = build("calendar", "v3", credentials=creds)

    def list_free_slots(self, start: datetime, end: datetime) -> List[Dict[str, str]]:
        """Return a list of free slots between `start` & `end` in ISO format."""

        # ✅ Ensure timezone-aware datetime in UTC
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

        # ✅ Ensure timezone-aware datetimes
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
